import random
from django.shortcuts import render
from django.http import HttpResponse
from twilio.rest import Client
import logging
# since we are not passing the csrf tocken when submiting a message, do the following:
from django.views.decorators.csrf import csrf_exempt

from .models import InventoryOrders, Session, UserSession
from django.utils import timezone
from datetime import timedelta
from datetime import datetime

account_sid = '[AccountSID]'
auth_token = '[AuthToken]'
client = Client(account_sid, auth_token)


greeting_messages = [
    "hi there",
    "hello",
    "hey",
    "hi",
    "good day",
    "howdy",
    "greetings",
    "what's up",
    "hi there!",
    "hey there",
    "hello there",
    "good morning",
    "good afternoon",
    "good evening",
    "welcome",
    "how's it going",
    "hey there!",
    "hiya",
    "hi everyone",
    "hello all",
    "hey all",
]

# List of session termination commands
termination_commands = ['exit', 'stop', 'end']



# Greeting filters based on time of day
def get_time_based_greeting():
    now = datetime.now().time()
    if now < datetime.strptime('12:00:00', '%H:%M:%S').time():
        # Morning
        return ["good morning", "hi there", "hello", "hey", "hi", "good day"]
    elif now < datetime.strptime('17:00:00', '%H:%M:%S').time():
        # Afternoon
        return ["good afternoon", "hi there", "hello", "hey", "hi", "good day"]
    else:
        # Evening
        return ["good evening", "hi there", "hello", "hey", "hi", "good day"]



# Create your views here.
@csrf_exempt
def bot(request):
     logging.basicConfig(filename='app.log', level=logging.ERROR)
     #print(request.POST)
     
     
     sender_name = request.POST["ProfileName"]
     sender_mobileno = request.POST.get('From', '')
     incoming_msg = request.POST.get('Body', '').lower()
     #message_type = request.POST["MessageType"]
     #message_status = request.POST["SmsStatus"]
     #message_sid = request.POST["SmsMessageSid"]

     # Retrieve or create a UserSession
     user_session, user_created = UserSession.objects.get_or_create(phone_number=sender_mobileno)

     # If the user session was created or if the username needs to be updated
     if user_created or user_session.whatsapp_username != sender_name:
          user_session.whatsapp_username = sender_name
          user_session.save()

     # Define default step or logic
     default_step = '0'  # Example default step, adjust as needed
     
     # Attempt to retrieve an active session for the user
     session = Session.objects.filter(user=user_session, status='active').order_by('-start_time').first()



     if session:
        # Check for timeout
        timeout_period = timedelta(minutes=30)
        if session.end_time is None:
          # If end_time is None, treat it as still active
          session.end_time = timezone.now()
          session.save()
        elif  timezone.now() - session.end_time > timeout_period:
            # Mark the session as expired
            session.status = 'expired'
            session.save()

            # Notify the user
            bye_response_msg = (f"Hi {sender_name}, it looks like your session timed out. Let’s start fresh—say hello and let’s chat!")

            client.messages.create(
                    body=bye_response_msg,
                    from_='whatsapp:+14155238886',
                    to=sender_mobileno
               )
            
            return HttpResponse("Session expired!")

            # Create a new session
            #session = Session.objects.create(user=user_session, start_time=timezone.now(), status='active')
     else:
        # No active session found, create a new one
        session = Session.objects.create(user=user_session, start_time=timezone.now(), end_time=timezone.now(), status='active')

     
     

     if session and incoming_msg not in termination_commands:
          session.end_time = timezone.now()
          session.save()


     
     # Check for explicit termination commands
     if incoming_msg in termination_commands:
          response_msg = "Your session has been terminated. Thank you for chatting with us. Have a great day!"
          # Mark the session as expired
          session.end_time = timezone.now()
          session.status = 'expired'
          session.save()
          client.messages.create(
               body=response_msg,
               from_='whatsapp:+14155238886',
               to=sender_mobileno
          )
          return HttpResponse("Session ended")

     # Update the timestamp of the last interaction
     session.save()

     # Get the appropriate greetings based on the time of day
     time_based_greetings = get_time_based_greeting()

     inventory_order, created = InventoryOrders.objects.get_or_create(session=session, defaults={'category': 'Unknown'})
     if session.step == '0':
          # Check if incoming message is in the filtered greetings
          if any(greeting in incoming_msg for greeting in greeting_messages):
               capitalized_greetings = [msg.capitalize() for msg in time_based_greetings]
               greeting_response_msg = random.choice(capitalized_greetings)
               client.messages.create(
                         from_='whatsapp:+14155238886',
                         body=f"""
                         👋 *{greeting_response_msg} {sender_name}*, \n\nWelcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,
                         to=sender_mobileno
                         )
               # Update session to step 1
               session.step = "1"
               session.save()
          else:
               capitalized_greetings = [msg.capitalize() for msg in time_based_greetings]
               greeting_response_msg = random.choice(capitalized_greetings)
               response_msg = f"""
               😢 Sorry {sender_name}, I didn't understand what you just typed above.\n\n However, 👋 *{greeting_response_msg}*, and welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
               """
         
               client.messages.create(
                         from_='whatsapp:+14155238886',
                         body=response_msg,
                         to=sender_mobileno
                         )
               # Update session to step 1
               session.step = "1"
               session.save()
               
     # Handle user options
     elif session.step == "1":
          if incoming_msg == '1':
               response_msg = f"""
                         *PLAWN AUTO PARTS BRANCHES*\n\n*Please select from any city/town listed below*, \n\nNote that we currently have active shops in the listed locations below. \n\n1️⃣ Harare\n2️⃣ Bulawayo\n3️⃣ Mutare\n4️⃣ Gweru\n5️⃣ Chinhoyi\n6️⃣ Kwekwe\n7️⃣ Masvingo \n8️⃣ Kadoma \n9️⃣ Zvishavane \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,
               # Update session to step 2 or a specific branch info step
               session.step = "1a"
               session.save()
          elif incoming_msg == '2':
               response_msg = f"""
                         *ORDER ITEMS IN STOCK*\n\n*Please select the type of part you are looking for from any category listed below*, \n\nWe’ve only listed a few products, not our entire inventory. If you can’t find what you need, please ask for help. \n\n1️⃣ Accessories \n2️⃣ Body Parts\n3️⃣ Drive Train\n4️⃣ Engine\n5️⃣ Filters\n6️⃣ Lubricants\n7️⃣ Suspension \n8️⃣ Tyres and Wheels \n9️⃣ Other \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,
               # Update session to step 3 or contact details step
               session.step = "2a"
               session.save()
          elif incoming_msg == '3':
               response_msg = f"""
                         *BOOK OUR SERVICES*\n\n*Please select service below to proceed with booking*, \n\n1️⃣ Disc Skimming \n2️⃣ Major Service \n3️⃣ Minor Service \n4️⃣ Press Fitting\n5️⃣ Spring Compression\n6️⃣ Suspension Fitting\n7️⃣ Tyre Fitting \n8️⃣ Wheel Balancing \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,
               # Update session to step 3 or contact details step
               session.step = "3a"
               session.save()
          elif incoming_msg == '4':
               response_msg = f"""
                         *ITEMS ON PROMOTION*\n\n*Please select items on promotion from the list below.* \n\n😬 Currently, there are no items running on promotion. Please stay tuned, as we’re preparing some exciting offers soon. \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,
               # Update session to step 3 or contact details step
               session.step = "4a"
               session.save()
          elif incoming_msg == '5':
               response_msg = f"""
                         *HOW TO ACCESS FREE DELIVERY*\n\n*Steps to Access Free Khonapo Delivery Service* \n\n- *Order Items Worth Over $30:* Ensure that the total value of your order is more than $30. \n- *Enter Delivery Information:* Provide your delivery address and any other required details.\n- *Select Free Delivery:* Choose the “Free Delivery” option during checkout. Make sure your order meets the minimum purchase requirement of $30.\n- *Confirm Your Order:* Review your order details and finalize the order.\n- *Receive Confirmation:* You’ll get an order confirmation with delivery information.\n- *Track Your Delivery:* Use the tracking feature on the website or app to monitor the status of your delivery. \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,
               # Update session to step 3 or contact details step
               session.step = "5a"
               session.save()
          elif incoming_msg == '6':
               response_msg = faq_text = """
                    FREQUENTLY ASKED QUESTIONS

                    Get a Taste of Our FAQs

                    1. What services do you offer?
                    We offer minor and major car servicing, tyre fitting, suspension fitting, wheel balancing, disc skimming, spring compression, and press fitting.

                    2. How often should I get my car serviced?
                    Minor service: every 6 months or 5,000-10,000 miles. Major service: every 12 months or 10,000-20,000 miles. Refer to your vehicle’s manual for specifics.

                    3. What’s the difference between minor and major service?
                    Minor service covers basic maintenance like oil changes. Major service includes additional checks and replacements.

                    4. How can I tell if my tyres need replacing?
                    Check tread depth; replace if below 1.6mm. Look for visible damage or uneven wear.

                    5. What does wheel balancing involve?
                    It ensures even weight distribution, reducing vibrations and preventing uneven tyre wear.

                    6. What is disc skimming?
                    Resurfacing brake discs to remove grooves and improve braking performance.

                    7. What is spring compression?
                    Adjusting and checking suspension springs for proper alignment and ride quality.

                    8. How can I book a service appointment?
                    Book via phone, email, or our website. We’ll schedule a convenient time.

                    9. What if I have a problem after a service?
                    Contact us immediately; we’ll resolve any issues promptly.

                    10. Do you offer warranties on your services?
                    Yes, we provide warranties on services and parts. Ask for details when booking.

                    More Options

                    *️⃣ Return to Previous Options
                    #️⃣ Return to Main Menu

                    If you want to end our chat, type _bye_, _exit_, or _end_. You can reach me anytime. 😉
                    """

               # Update session to step 3 or contact details step
               session.step = "5a"
               session.save()
          else:
               capitalized_greetings = [msg.capitalize() for msg in time_based_greetings]
               greeting_response_msg = random.choice(capitalized_greetings)
               response_msg = f"""
               😢 Sorry, {sender_name}, the option you entered is not valid. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
               """
          # Send response
          client.messages.create(
               body=response_msg,
               from_='whatsapp:+14155238886',
               to=sender_mobileno
          )

     #### BRANCH LOCATIONS
     elif session.step == "1a":
          if incoming_msg == '1':
               response_msg = f"""
               *HARARE - BRANCHES*\n\n*Reach out to any branch below and get assisted.* \n\n*Graniteside Branch*\n🏢 35 Sande Crescent, Graniteside, Harare \n📞 +263 71 973 5735 \n\n*Kaguvi Street Branch A*\n🏢 55 Kaguvi Street, Harare \n📞 +263 78 015 6144 \n\n*Msasa Branch*\n🏢 69 Stevens Drive Msasa, Harare \n📞 +263 77 984 5936 \n\n*Kaguvi Street Branch B*\n🏢 24 Kaguvi Street, Harare \n📞 +263 77 925 6275 \n\n*Eastlea Branch*\n🏢 No. 1 Mc chlery Avenue Eastlea, Harare \n📞 +263 77 759 0534 \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
               """
               # Update session to step 1
               session.step = "1a1"
               session.save()

          elif incoming_msg == '2':
               response_msg = f"""
               *BULAWAYO - BRANCHES*\n\n*Reach out to any branch below and get assisted.* \n\n*Bulawayo Branch A*\n🏢 255 Jason Moyo Ave Btwn 12th & 13th Ave Shop 4, Bulawayo \n📞 +263 77 984 5938 \n\n*Bulawayo Branch B*\n🏢 Shop 5, Ambika 4th Ave Btwn Fort & JM St, Bulawayo \n📞 +263 71 984 5937 \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
               """
               # Update session to step 1
               session.step = "1a1"
               session.save()
          elif incoming_msg == '3':
               response_msg = f"""
               *MUTARE - BRANCH*\n\n*Reach out to our branch below and get assisted.* \n\n*Mutare Branch A*\n🏢 55 First Street,, Mutare \n📞 +263 77 401 6666 \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
               """
               # Update session to step 1
               session.step = "1a1"
               session.save()
          elif incoming_msg == '4':
               response_msg = f"""
               *GWERU - BRANCH*\n\n*Reach out to our branch below and get assisted.* \n\n*Gweru Branch*\n🏢 27 Third Street Bhanditi Complex, Gweru \n📞 +263 78 957 3722 \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
               """
               # Update session to step 1
               session.step = "1a1"
               session.save()
          elif incoming_msg == '5':
               response_msg = f"""
               *CHINHOYI - BRANCH*\n\n*Reach out to our branch below and get assisted.* \n\n*Chinhoyi Branch*\n🏢 5346 Midway Street, Chinhoyi \n📞 +263 71 984 5938 \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
               """
               # Update session to step 1
               session.step = "1a1"
               session.save()
          elif incoming_msg == '6':
               response_msg = f"""
               *KWEKWE - BRANCH*\n\n*Reach out to our branch below and get assisted.* \n\n*Kwekwe Branch*\n🏢 No. 8 Essats Building Cnr RG Mugabe & Kings Ave, Kwekwe \n📞 +263 78 873 1747 \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
               """
               # Update session to step 1
               session.step = "1a1"
               session.save()
          elif incoming_msg == '7':
               response_msg = f"""
               *MASVINGO - BRANCH*\n\n*Reach out to our branch below and get assisted.* \n\n*Masvingo Branch*\n🏢 29 Shuvai Mahofa Liquids Complex Masvingo \n📞 +263 78 977 7666 \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
               """
               # Update session to step 1
               session.step = "1a1"
               session.save()
          elif incoming_msg == '8':
               response_msg = f"""
               *KADOMA - BRANCH*\n\n*Reach out to our branch below and get assisted.* \n\n*Kadoma Branch*\n🏢 K Cnr, Corner Robert Mugabe and Chakari Road Shop 9, Kadoma \n📞 +263 77 843 0120 \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
               """
               # Update session to step 1
               session.step = "1a1"
               session.save()
          elif incoming_msg == '9':
               response_msg = f"""
               *ZVISHAVANE - BRANCH*\n\n*Reach out to our branch below and get assisted.* \n\n*Zvishavane Branch*\n🏢 3723 Mandava (Next To LaLiga Bar), Zvishavane \n📞 +263 78 596 1381 \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
               """
               # Update session to step 1
               session.step = "1a1"
               session.save()
          elif incoming_msg == '*':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          elif incoming_msg == '#':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          else:
               response_msg = f"""
                         *PLAWN AUTO PARTS BRANCHES*\n\n*😢 Sorry, {sender_name}, the option you entered is not valid. Please select from any city/town listed below*, \n\nNote that we currently have active shops in the listed locations below. \n\n1️⃣ Harare\n2️⃣ Bulawayo\n3️⃣ Mutare\n4️⃣ Gweru\n5️⃣ Chinhoyi\n6️⃣ Kwekwe\n7️⃣ Masvingo \n8️⃣ Kadoma \n9️⃣ Zvishavane \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,

          # Send response
          client.messages.create(
               body=response_msg,
               from_='whatsapp:+14155238886',
               to=sender_mobileno
          )
     #### BRANCH INDIVIDUALS
     elif session.step == "1a1":
          if incoming_msg == '*':
               response_msg = f"""
                                   *PLAWN AUTO PARTS BRANCHES*\n\n*Please select from any city/town listed below*, \n\nNote that we currently have active shops in the listed locations below. \n\n1️⃣ Harare\n2️⃣ Bulawayo\n3️⃣ Mutare\n4️⃣ Gweru\n5️⃣ Chinhoyi\n6️⃣ Kwekwe\n7️⃣ Masvingo \n8️⃣ Kadoma \n9️⃣ Zvishavane \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                                   """,
                         # Update session to step 2 or a specific branch info step
               session.step = "1a"
               session.save()
          elif incoming_msg == '#':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          else:
               response_msg = f"""
                                   *PLAWN AUTO PARTS BRANCHES*\n\n*Please select from any city/town listed below*, \n\nNote that we currently have active shops in the listed locations below. \n\n1️⃣ Harare\n2️⃣ Bulawayo\n3️⃣ Mutare\n4️⃣ Gweru\n5️⃣ Chinhoyi\n6️⃣ Kwekwe\n7️⃣ Masvingo \n8️⃣ Kadoma \n9️⃣ Zvishavane \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                                   """,
                         # Update session to step 2 or a specific branch info step
               session.step = "1a"
               session.save()
          # Send response
          client.messages.create(
               body=response_msg,
               from_='whatsapp:+14155238886',
               to=sender_mobileno
          )
     elif session.step == "2a":
          category_mapping = {
            '1': 'Accessories',
            '2': 'Body Parts',
            '3': 'Drive Train',
            '4': 'Engine',
            '5': 'Filters',
            '6': 'Lubricants',
            '7': 'Suspension',
            '8': 'Tyres and Wheels',
            '9': 'Other'
          }
          if incoming_msg in category_mapping:
               inventory_order.category = category_mapping[incoming_msg]
               inventory_order.save()

               response_msg = f"""
                         *ORDER ITEMS IN STOCK*\n\n*Great! Please type the name of the specific part you need (e.g., brake pad, air filter, spark plug).*, \n\n\n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,
               # Update session to step 1
               session.step = "2b"
               session.save()
          elif incoming_msg == '*':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          elif incoming_msg == '#':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          else:
               response_msg = f"""
                         *ORDER ITEMS IN STOCK*\n\n*Sorry, {sender_name}, the option you entered is not valid. Please select from any category listed below*, \n\nWe’ve only listed a few products, not our entire inventory. If you can’t find what you need, please ask for help. \n\n1️⃣ Accessories \n2️⃣ Body Parts\n3️⃣ Drive Train\n4️⃣ Engine\n5️⃣ Filters\n6️⃣ Lubricants\n7️⃣ Suspension \n8️⃣ Tyres and Wheels \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,

          # Send response
          client.messages.create(
               body=response_msg,
               from_='whatsapp:+14155238886',
               to=sender_mobileno
          )
     elif session.step == "2b":
          if incoming_msg != '':
               # Update part_name based on incoming message
               if incoming_msg:
                    inventory_order.part_name = incoming_msg
                    inventory_order.save()
               response_msg = f"""
                         *ORDER ITEMS IN STOCK*\n\n*What is the make of your vehicle or equipment? (e.g., Toyota, Ford, Honda)*, \n\n\n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,
               # Update session to step 1
               session.step = "2c"
               session.save()
          elif incoming_msg == '*':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          elif incoming_msg == '#':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          else:
               response_msg = f"""
                         *ORDER ITEMS IN STOCK*\n\n*Sorry, {sender_name}, the option you entered is not valid. Please select from any category listed below*, \n\nWe’ve only listed a few products, not our entire inventory. If you can’t find what you need, please ask for help. \n\n1️⃣ Accessories \n2️⃣ Body Parts\n3️⃣ Drive Train\n4️⃣ Engine\n5️⃣ Filters\n6️⃣ Lubricants\n7️⃣ Suspension \n8️⃣ Tyres and Wheels \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,

          # Send response
          client.messages.create(
               body=response_msg,
               from_='whatsapp:+14155238886',
               to=sender_mobileno
          )
     elif session.step == "2c":
          if incoming_msg != '':
               # Update part_name based on incoming message
               if incoming_msg:
                    inventory_order.vehicle_make = incoming_msg
                    inventory_order.save()
               response_msg = f"""
                         *ORDER ITEMS IN STOCK*\n\n*Almost there! Please provide the specific model of your vehicle or equipment (e.g., Camry, F-150, Civic).*, \n\n\n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,
               # Update session to step 1
               session.step = "2d"
               session.save()
          elif incoming_msg == '*':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          elif incoming_msg == '#':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          else:
               response_msg = f"""
                         *ORDER ITEMS IN STOCK*\n\n*Sorry, {sender_name}, the option you entered is not valid. Please select from any category listed below*, \n\nWe’ve only listed a few products, not our entire inventory. If you can’t find what you need, please ask for help. \n\n1️⃣ Accessories \n2️⃣ Body Parts\n3️⃣ Drive Train\n4️⃣ Engine\n5️⃣ Filters\n6️⃣ Lubricants\n7️⃣ Suspension \n8️⃣ Tyres and Wheels \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,

          # Send response
          client.messages.create(
               body=response_msg,
               from_='whatsapp:+14155238886',
               to=sender_mobileno
          )
     elif session.step == "2d":
          if incoming_msg != '':
               # Update part_name based on incoming message
               if incoming_msg:
                    inventory_order.vehicle_model = incoming_msg
                    inventory_order.save()
               response_msg = f"""
                         *ORDER ITEMS IN STOCK*\n\n*Great! Finally, what is the year of manufacture for your vehicle? (e.g., 2019, 2020)*, \n\n\n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,
               # Update session to step 1
               session.step = "2e"
               session.save()
          elif incoming_msg == '*':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          elif incoming_msg == '#':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          else:
               response_msg = f"""
                         *ORDER ITEMS IN STOCK*\n\n*Sorry, {sender_name}, the option you entered is not valid. Please select from any category listed below*, \n\nWe’ve only listed a few products, not our entire inventory. If you can’t find what you need, please ask for help. \n\n1️⃣ Accessories \n2️⃣ Body Parts\n3️⃣ Drive Train\n4️⃣ Engine\n5️⃣ Filters\n6️⃣ Lubricants\n7️⃣ Suspension \n8️⃣ Tyres and Wheels \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,

          # Send response
          client.messages.create(
               body=response_msg,
               from_='whatsapp:+14155238886',
               to=sender_mobileno
          )
     elif session.step == "2e":
          if incoming_msg != '':
               # Update part_name based on incoming message
               if incoming_msg:
                    inventory_order.manufacturer_year = incoming_msg
                    inventory_order.save()
               response_msg = f"""
                         *ORDER ITEMS IN STOCK*\n\n*Thank you! I’ll have a member of our sales team find the parts you requested and get back to you shortly. If the part is available, we can also arrange free delivery for you. Would you like us to include delivery?*, \n\n1️⃣ Yes, please include free delivery. \n2️⃣ No, I will collect it at the branch. \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,
               # Update session to step 1
               session.step = "2f"
               session.save()
          elif incoming_msg == '*':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          elif incoming_msg == '#':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          else:
               response_msg = f"""
                         *ORDER ITEMS IN STOCK*\n\n*Sorry, {sender_name}, the option you entered is not valid. Please select from any category listed below*, \n\nWe’ve only listed a few products, not our entire inventory. If you can’t find what you need, please ask for help. \n\n1️⃣ Accessories \n2️⃣ Body Parts\n3️⃣ Drive Train\n4️⃣ Engine\n5️⃣ Filters\n6️⃣ Lubricants\n7️⃣ Suspension \n8️⃣ Tyres and Wheels \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,

          # Send response
          client.messages.create(
               body=response_msg,
               from_='whatsapp:+14155238886',
               to=sender_mobileno
          )

     elif session.step == "2f":
          if incoming_msg == '1':
               # Update delivery based on incoming message
               if incoming_msg:
                    inventory_order.delivery = incoming_msg
                    inventory_order.save()
               response_msg = f"""
                         *ORDER ITEMS IN STOCK*\n\n*Perfect! Free delivery is on us. Your items will be shipped directly to you.*, \n\n Type # to go back to the menu and choose option 8 to create an account. This will make chatting with us easier and speed up many processes. Plus, there are lots of benefits to creating an account! \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,
               # Update session to step 1
               session.step = "2f"
               session.save()
          elif incoming_msg == '2':
               # Update delivery based on incoming message
               if incoming_msg:
                    inventory_order.delivery = incoming_msg
                    inventory_order.save()
               response_msg = f"""
                         *ORDER ITEMS IN STOCK*\n\n*Got it! You can pick up your order at our branch. We’ll have it ready for you.*, \n\n Type # to go back to the menu and choose option 8 to create an account. This will make chatting with us easier and speed up many processes. Plus, there are lots of benefits to creating an account! \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,
               # Update session to step 1
               session.step = "2f"
               session.save()
          elif incoming_msg == '*':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          elif incoming_msg == '#':
               response_msg = f"""
                         Welcome to Plawn Motors, your source for genuine, affordable auto parts with express fitment centers and free delivery. \n\n*Please select any number (🔢) from the following options below and get assistance.*\n\n1️⃣ Contact our Branches \n2️⃣ Order Items instock \n3️⃣ Book our Services \n4️⃣ Items on Promotion \n5️⃣ How to access Free Deliveries \n6️⃣ Frequently Asked Questions \n\n*More Options*\n\n7️⃣ My Orders \n8️⃣ Register/Login for more \n9️⃣ Visit our Website \n🔟 Submit Feedback/Rate us \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """
               # Update session to step 1
               session.step = "1"
               session.save()
          else:
               response_msg = f"""
                         *ORDER ITEMS IN STOCK*\n\n*Sorry, {sender_name}, the option you entered is not valid. Please select from any category listed below*, \n\nWe’ve only listed a few products, not our entire inventory. If you can’t find what you need, please ask for help. \n\n1️⃣ Accessories \n2️⃣ Body Parts\n3️⃣ Drive Train\n4️⃣ Engine\n5️⃣ Filters\n6️⃣ Lubricants\n7️⃣ Suspension \n8️⃣ Tyres and Wheels \n\n*More Options*\n\n*️⃣ Return to Previous Options \n#️⃣ Return to Main Menu \n\n\nIf you want to end our chat, don't hesitate to type _bye_, _exit_, or _end_. You can still reach me whenever you want my assistance.😉 \n\n
                         """,

          # Send response
          client.messages.create(
               body=response_msg,
               from_='whatsapp:+14155238886',
               to=sender_mobileno
          )

     

          



     return HttpResponse("Message sent")


