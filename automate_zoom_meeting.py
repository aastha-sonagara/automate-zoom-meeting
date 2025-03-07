from datetime import datetime, timedelta, timezone
import csv
import os
import re
import requests
import base64

# Constants
DATABASE_FILE = r"C:\Users\aasth\Downloads\meetings.csv"
MEETING_DURATION_MINUTES = 60  # Meeting duration in minutes
IST = timezone(timedelta(hours=5, minutes=30))  # Indian Standard Time

executive_details = {
    'aastha_sonagara': {'client_id': 'lDZaabEKTdq0508BeFGkDw', 'client_secret': 'CiLcEAiPBo886Ai7iEbBFQm67Rjkc7U8', 'email': 'aastha1693@gmail.com', 'account_id': '_KaufKcyQ7GN-Fb3fp5luQ'}
    
    # Add more executives if needed
}

# Initialize executives' availability
executives_availability = {executive: [] for executive in executive_details}

def get_access_token(executive):
    credentials = executive_details[executive]
    client_id = credentials['client_id']
    client_secret = credentials['client_secret']
    account_id = credentials['account_id']
    oauth_url = f'https://zoom.us/oauth/token?grant_type=account_credentials&account_id={account_id}'

    try:
        auth_header = f'Basic {base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()}'
        headers = {'Authorization': auth_header}
        response = requests.post(oauth_url, headers=headers)
        if response.status_code == 200:
            oauth_response = response.json()
            access_token = oauth_response.get('access_token')
            return access_token
        else:
            print(f'OAuth Request Failed with Status Code: {response.status_code}')
            print(response.text)
            return None
    except Exception as e:
        print(f'An error occurred: {str(e)}')
        return None

def get_my_user_id(access_token, email):
    list_users_url = 'https://api.zoom.us/v2/users?status=active'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(list_users_url, headers=headers)
    if response.status_code == 200:
        users_response = response.json()
        users = users_response.get('users', [])
        for user in users:
            if user.get('email').strip().lower() == email.strip().lower():
                return user.get('id')
        print(f"No user found for email: {email}")
        return None
    else:
        print(f'Failed to retrieve users: {response.status_code}')
        print(response.text)
        return None

def create_meeting(access_token, user_id, scheduled_start_time):
    create_meeting_url = f'https://api.zoom.us/v2/users/{user_id}/meetings'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    meeting_details = {
        "topic": "Client Meeting",
        "type": 2,
        "start_time": scheduled_start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": MEETING_DURATION_MINUTES,
        "timezone": "Asia/Kolkata",
        "settings": {
            "host_video": True,
            "participant_video": True
        }
    }
    response = requests.post(create_meeting_url, headers=headers, json=meeting_details)
    if response.status_code == 201:
        meeting_response = response.json()
        return meeting_response
    else:
        print(f"Failed to create meeting. HTTP Status Code: {response.status_code}")
        print(response.text)
        return None

def is_valid_mobile_number(mobile_number):
    return re.match(r'^[6-9]\d{9}$', mobile_number) is not None

def is_valid_email(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

def is_slot_taken(requested_start_time, requested_end_time):
    for executive in executives_availability:
        meetings = executives_availability[executive]
        for meeting in meetings:
            start_time = datetime.strptime(meeting['Meeting Start Time'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            end_time = datetime.strptime(meeting['Meeting End Time'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            if requested_start_time < end_time and requested_end_time > start_time:
                return True
    return False

def find_available_slots(requested_start_time, requested_end_time):
    available_slots = []
    max_days_ahead = 30
    current_time = datetime.now(timezone.utc)

    while requested_start_time < current_time + timedelta(days=max_days_ahead):
        if requested_start_time.weekday() in {5, 6}:  # Skip weekends
            requested_start_time += timedelta(days=(7 - requested_start_time.weekday()))
            continue

        while requested_start_time + timedelta(minutes=MEETING_DURATION_MINUTES) <= requested_end_time:
            if not is_slot_taken(requested_start_time, requested_start_time + timedelta(minutes=MEETING_DURATION_MINUTES)):
                available_slots.append((requested_start_time, requested_start_time + timedelta(minutes=MEETING_DURATION_MINUTES)))
            requested_start_time += timedelta(hours=1)

        requested_start_time += timedelta(days=1)
        requested_start_time = requested_start_time.replace(hour=9, minute=0)  # Reset to 9 AM for the next day

    return available_slots

def schedule_meeting(client_name, client_mobile_number, client_email_address, scheduled_start_time, scheduled_end_time):
    access_token = get_access_token('aastha_sonagara')  # Assuming using aastha_sonagara for scheduling
    if access_token:
        my_user_id = get_my_user_id(access_token, executive_details['aastha_sonagara']['email'])
        if my_user_id:
            meeting_response = create_meeting(access_token, my_user_id, scheduled_start_time)
            if meeting_response:
                meet_link = meeting_response.get('join_url')
                passcode = meeting_response.get('password')
                executives_availability['aastha_sonagara'].append({'Meeting Start Time': scheduled_start_time.strftime('%Y-%m-%d %H:%M:%S'), 'Meeting End Time': scheduled_end_time.strftime('%Y-%m-%d %H:%M:%S')})
                with open(DATABASE_FILE, 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=['Name', 'Mobile Number', 'Email Address', 'Meeting Start Time', 'Meeting End Time', 'Meeting Link', 'Passcode', 'Executive'])
                    writer.writerow({
                        'Name': client_name,
                        'Mobile Number': client_mobile_number,
                        'Email Address': client_email_address,
                        'Meeting Start Time': scheduled_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'Meeting End Time': scheduled_end_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'Meeting Link': meet_link,
                        'Passcode': passcode,
                        'Executive': 'aastha_sonagara'
                    })
                print(f"Meeting successfully scheduled with aastha_sonagara. Details - Date: {scheduled_start_time.strftime('%Y-%m-%d')}, Time: {scheduled_start_time.strftime('%H:%M:%S')} IST, Link: {meet_link}, Passcode: {passcode}")
                return meet_link, passcode, scheduled_start_time, scheduled_end_time
            else:
                print("Failed to schedule the meeting.")
                return None, None, None, None
        else:
            print("Failed to retrieve user ID.")
            return None, None, None, None
    else:
        print("Failed to get access token.")
        return None, None, None, None

def get_client_info():
    print("Hello! I am here to assist you by scheduling a 1-hour meeting with our member.")
    client_name = input("Could you please provide your full name? ")
    client_mobile_number = input("What's your mobile number (10 digits)?: ")
    while not is_valid_mobile_number(client_mobile_number):
        client_mobile_number = input("That mobile number is invalid. Please enter a valid 10-digit mobile number: ")
    client_email_address = input("What's your email address?: ")
    while not is_valid_email(client_email_address):
        client_email_address = input("That email address is invalid. Please enter a valid email address: ")
    date_str = input("On what date are you looking to schedule your meeting? (DD-MM-YYYY): ")
    start_time_str = input("From what time are you available? (HH, 24-hour format, e.g., '13' for 1 PM): ")
    end_time_str = input("Until what time are you available? (HH, 24-hour format, e.g., '14' for 2 PM): ")

    try:
        day, month, year = map(int, date_str.split('-'))
        start_hour = int(start_time_str)
        end_hour = int(end_time_str)
        requested_start_time = datetime(year, month, day, start_hour, 0, tzinfo=timezone.utc)
        requested_end_time = datetime(year, month, day, end_hour, 0, tzinfo=timezone.utc)

        if requested_start_time >= requested_end_time:
            print("Invalid time range provided. The start time must be earlier than the end time.")
            return

        available_slots = find_available_slots(requested_start_time, requested_end_time)
        if available_slots:
            print("Available slots for your requested time range:")
            for idx, (start_time, end_time) in enumerate(available_slots, 1):
                print(f"{idx}. {start_time.strftime('%Y-%m-%d %H:%M:%S')} to {end_time.strftime('%H:%M:%S')}")
            slot_choice = int(input(f"Please choose a slot by entering the corresponding number (1-{len(available_slots)}): "))
            chosen_slot = available_slots[slot_choice - 1]
            scheduled_start_time, scheduled_end_time = chosen_slot
            meet_link, passcode, start_time, end_time = schedule_meeting(client_name, client_mobile_number, client_email_address, scheduled_start_time, scheduled_end_time)
            if meet_link:
                print(f"Your meeting is scheduled successfully! Meeting link: {meet_link}, Passcode: {passcode}, Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}, End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("Failed to schedule your meeting. Please try again.")
        else:
            print("No available slots found for your requested time range. Please try another time range.")
    except ValueError:
        print("Invalid input provided. Please enter the date and time in the correct format.")
        return

def schedule_meeting(client_name, client_mobile_number, client_email_address, scheduled_start_time, scheduled_end_time):
    access_token = get_access_token('aastha_sonagara')  # Assuming using aastha_sonagara for scheduling
    if access_token:
        my_user_id = get_my_user_id(access_token, executive_details['aastha_sonagara']['email'])
        if my_user_id:
            meeting_response = create_meeting(access_token, my_user_id, scheduled_start_time)
            if meeting_response:
                meet_link = meeting_response.get('join_url')
                passcode = meeting_response.get('password')
                executives_availability['aastha_sonagara'].append({'Meeting Start Time': scheduled_start_time.strftime('%Y-%m-%d %H:%M:%S'), 'Meeting End Time': scheduled_end_time.strftime('%Y-%m-%d %H:%M:%S')})
                with open(DATABASE_FILE, 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=['Name', 'Mobile Number', 'Email Address', 'Meeting Start Time', 'Meeting End Time', 'Meeting Link', 'Passcode', 'Executive'])
                    writer.writerow({
                        'Name': client_name,
                        'Mobile Number': client_mobile_number,
                        'Email Address': client_email_address,
                        'Meeting Start Time': scheduled_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'Meeting End Time': scheduled_end_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'Meeting Link': meet_link,
                        'Passcode': passcode,
                        'Executive': 'aastha_sonagara'
                    })
                print(f"Meeting successfully scheduled with aastha_sonagara.")
                return meet_link, passcode, scheduled_start_time, scheduled_end_time
            else:
                print("Failed to schedule the meeting.")
                return None, None, None, None
        else:
            print("Failed to retrieve user ID.")
            return None, None, None, None
    else:
        print("Failed to get access token.")
        return None, None, None, None

if not os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['Name', 'Mobile Number', 'Email Address', 'Meeting Start Time', 'Meeting End Time', 'Meeting Link', 'Passcode', 'Executive'])
        writer.writeheader()

get_client_info()