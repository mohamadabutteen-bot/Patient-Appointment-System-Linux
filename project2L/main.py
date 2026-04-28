import os
import shutil
from datetime import datetime

# --- Define file and folder names as constants for easy modification ---
DOCTORS_FILE = 'doctors.txt'
PATIENTS_FILE = 'patients.txt'
APPOINTMENTS_FILE = 'appointments.txt'
LOG_FILE = 'system.log'
BACKUP_DIR = 'backups'


# --- Helper Functions ---

def log_action(action_details):
    """
    Log any important action in the log file with a timestamp.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] - {action_details}\n")


def check_files():
    """
    Check if essential data files exist before starting any operation.
    """
    for file in [DOCTORS_FILE, PATIENTS_FILE, APPOINTMENTS_FILE, LOG_FILE]:
        if not os.path.exists(file):
            open(file, 'w', encoding='utf-8').close()
            log_action(f"WARNING: File '{file}' not found, created a new empty file.")
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        log_action(f"INFO: Backup directory '{BACKUP_DIR}' created.")


def get_next_id(filename):
    """
    Generate a new unique ID (for doctor, patient, or appointment)
    by reading the last ID and incrementing it.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if not lines:
                return 1
            last_line = lines[-1].strip()
            if not last_line:
                for i in range(len(lines) - 2, -1, -1):
                    if lines[i].strip():
                        last_line = lines[i].strip()
                        break
                else:
                    return 1
            last_id = int(last_line.split('|')[0])
            return last_id + 1
    except (IOError, IndexError, ValueError):
        return 1


def validate_date(date_str):
    """
    Validate that the entered date follows the format YYYY-MM-DD.
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_time(time_str):
    """
    Validate that the entered time follows the format HH:MM.
    """
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False


def validate_and_normalize_days(days_str):
    """
    Validate comma-separated days and normalize them to TitleCase.
    Returns a normalized string of days or None if validation fails.
    """
    valid_days = {'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'}
    day_list = [day.strip().title() for day in days_str.split(',')]

    for day in day_list:
        if day not in valid_days:
            print(f"Error: '{day}' is not a valid day of the week.")
            return None

    return ",".join(day_list)


# --- Patient Services ---

def register_new_patient():
    """
    Register a new patient by entering their name and phone number,
    and generate a unique ID. Includes validation.
    """
    print("\n--- Register New Patient ---")
    while True:
        name = input("Enter patient's full name: ").strip()
        if name:
            break
        print("Error: Name cannot be empty.")

    while True:
        phone = input("Enter patient's phone number (digits only): ").strip()
        if phone.isdigit():
            break
        print("Error: Phone number must contain digits only.")

    patient_id = get_next_id(PATIENTS_FILE)

    with open(PATIENTS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{patient_id}|{name}|{phone}\n")

    log_action(f"PATIENT_REGISTRATION: New patient registered with ID {patient_id}, Name: {name}")
    print(f"Patient registered successfully! Your patient ID is: {patient_id}")


def book_new_appointment():
    """
    Book a new appointment for a patient with a doctor, checking for conflicts.
    Patients first search doctors by specialty. Includes validation.
    """
    print("\n--- Book New Appointment ---")
    patient_id_str = input("Enter your Patient ID: ").strip()
    if not patient_id_str.isdigit():
        print("Error: Patient ID must be a number.")
        return

    search_specialty = input(
        "Enter the specialty you are looking for (e.g., Cardiology, Dermatology): ").strip().lower()

    try:
        with open(DOCTORS_FILE, 'r', encoding='utf-8') as f:
            print("\n--- Available Doctors ---")
            doctors = f.readlines()
            matching_doctors = []
            if not doctors:
                print("No doctors are currently registered in the system.")
                return
            for doc in doctors:
                parts = doc.strip().split('|')
                if len(parts) >= 6 and search_specialty in parts[2].lower():
                    matching_doctors.append(parts)
                    print(
                        f"ID: {parts[0]}, Doctor: {parts[1]}, Specialty: {parts[2]}, Availability: {parts[3]} from {parts[4]} to {parts[5]}")

            if not matching_doctors:
                print(f"No doctors found with the specialty '{search_specialty}'.")
                return

    except FileNotFoundError:
        print(f"Error: Doctors file '{DOCTORS_FILE}' not found.")
        return

    while True:
        doctor_id_str = input("\nEnter the Doctor ID you want to book with: ").strip()
        if doctor_id_str.isdigit():
            break
        print("Error: Doctor ID must be a number.")

    while True:
        date_str = input("Enter appointment date (YYYY-MM-DD): ").strip()
        if validate_date(date_str):
            break
        print("Error: Invalid date format. It must be YYYY-MM-DD.")

    while True:
        time_str = input("Enter appointment time (HH:MM in 24-hour format): ").strip()
        if validate_time(time_str):
            break
        print("Error: Invalid time format. It must be HH:MM.")

    try:
        doctor_info = None
        with open(DOCTORS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('|')
                if parts and parts[0] == doctor_id_str:
                    doctor_info = parts
                    break
        if not doctor_info or len(doctor_info) < 6:
            print("Error: No doctor found with this ID or doctor data is incomplete.")
            return

        _, _, _, available_days_str, start_time, end_time = doctor_info

        appointment_day = datetime.strptime(date_str, '%Y-%m-%d').strftime('%A')
        if appointment_day not in available_days_str.split(','):
            print(f"Error: Doctor is not available on {appointment_day}. Available days: {available_days_str}")
            return

        appointment_time_obj = datetime.strptime(time_str, '%H:%M').time()
        if not (datetime.strptime(start_time, '%H:%M').time() <= appointment_time_obj < datetime.strptime(end_time,
                                                                                                          '%H:%M').time()):
            print(f"Error: Appointment time is outside doctor's working hours ({start_time} - {end_time}).")
            return

        with open(APPOINTMENTS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) == 6:
                    app_doc_id, app_date, app_time, status = parts[2], parts[3], parts[4], parts[5]
                    if app_doc_id == doctor_id_str and app_date == date_str and app_time == time_str and status == 'Confirmed':
                        print("Error: This time slot is already booked. Please choose another time.")
                        return

        appointment_id = get_next_id(APPOINTMENTS_FILE)
        with open(APPOINTMENTS_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{appointment_id}|{patient_id_str}|{doctor_id_str}|{date_str}|{time_str}|Confirmed\n")

        log_action(
            f"APPOINTMENT_BOOKING: Appointment ID {appointment_id} for Patient ID {patient_id_str} with Doctor ID {doctor_id_str}.")
        print("Appointment booked successfully!")

    except Exception as e:
        print(f"Unexpected error occurred: {e}")


def view_appointment_history():
    """
    View appointment history for a specific patient (confirmed or cancelled).
    """
    print("\n--- View My Appointments ---")
    patient_id_str = input("Enter your Patient ID: ").strip()

    if not patient_id_str.isdigit():
        print("Error: Patient ID must be a number.")
        return

    patient_id = int(patient_id_str)
    found = False

    print("\n--- Your Appointments ---")
    try:
        with open(APPOINTMENTS_FILE, 'r', encoding='utf-8') as app_f, \
                open(DOCTORS_FILE, 'r', encoding='utf-8') as doc_f:

            doctors_data = {line.split('|')[0]: line.strip().split('|') for line in doc_f if line.strip()}

            for app_line in app_f:
                line = app_line.strip()
                if not line:
                    continue
                parts = line.split('|')
                # Check for correct format before converting to int
                if len(parts) == 6 and parts[1].isdigit() and int(parts[1]) == patient_id:
                    found = True
                    app_id, _, doc_id, date, time, status = parts
                    doc_info = doctors_data.get(doc_id)
                    if doc_info and len(doc_info) >= 3:
                        doc_name = doc_info[1]
                        doc_spec = doc_info[2]
                        print(
                            f"Appointment ID: {app_id}, Doctor: {doc_name} ({doc_spec}), Date: {date}, Time: {time}, Status: {status}")
                    else:
                        print(
                            f"Appointment ID: {app_id}, Unknown Doctor (ID: {doc_id}), Date: {date}, Time: {time}, Status: {status}")

    except FileNotFoundError:
        print("Error: Cannot access data files.")
        return

    if not found:
        print("No appointments found for this patient.")


def cancel_appointment():
    """
    Cancel an upcoming appointment and change its status to "Cancelled".
    """
    print("\n--- Cancel Appointment ---")
    patient_id_str = input("Enter your Patient ID: ").strip()
    if not patient_id_str.isdigit():
        print("Error: Patient ID must be a number.")
        return
    patient_id = int(patient_id_str)

    appointment_id_str = input("Enter the Appointment ID you want to cancel: ").strip()
    if not appointment_id_str.isdigit():
        print("Error: Appointment ID must be a number.")
        return
    appointment_id = int(appointment_id_str)

    try:
        with open(APPOINTMENTS_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        updated_lines = []
        found = False
        modified = False
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue  # Skip empty lines

            parts = stripped_line.split('|')
            # Add validation before int conversion
            if len(parts) == 6 and parts[0].isdigit() and parts[1].isdigit() and \
                    int(parts[0]) == appointment_id and int(parts[1]) == patient_id:
                found = True
                if parts[5].lower() == 'confirmed':
                    parts[5] = 'Cancelled'
                    updated_lines.append("|".join(parts) + "\n")
                    modified = True
                    log_action(
                        f"APPOINTMENT_CANCEL: Appointment ID {appointment_id} for Patient ID {patient_id} was cancelled.")
                    print("Appointment cancelled successfully.")
                else:
                    updated_lines.append(line)
                    print(f"Cannot cancel this appointment because its status is '{parts[5]}', not 'Confirmed'.")
            else:
                updated_lines.append(line)

        if found and modified:
            with open(APPOINTMENTS_FILE, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
        elif not found:
            print("No appointment found with this ID for this patient.")

    except FileNotFoundError:
        print("Error: Cannot access appointments file.")


# --- Admin Services ---

def add_new_doctor():
    """
    Add a new doctor to the system with specialty, available days, and working hours.
    Includes comprehensive validation.
    """
    print("\n--- Add New Doctor ---")
    while True:
        name = input("Enter doctor's name: ").strip()
        if name:
            break
        print("Error: Doctor's name cannot be empty.")

    while True:
        specialty = input("Enter doctor's specialty: ").strip()
        if specialty:
            break
        print("Error: Specialty cannot be empty.")

    while True:
        days_input = input("Enter available days (Example: Sunday,Tuesday,Friday): ").strip()
        available_days = validate_and_normalize_days(days_input)
        if available_days:
            break

    while True:
        start_time = input("Enter start time (24-hour format, Example: 09:00): ").strip()
        if validate_time(start_time):
            break
        print("Error: Invalid time format. It must be HH:MM.")

    while True:
        end_time = input("Enter end time (24-hour format, Example: 17:00): ").strip()
        if validate_time(end_time):
            if datetime.strptime(end_time, '%H:%M') > datetime.strptime(start_time, '%H:%M'):
                break
            else:
                print("Error: End time must be after start time.")
        else:
            print("Error: Invalid time format. It must be HH:MM.")

    doctor_id = get_next_id(DOCTORS_FILE)
    with open(DOCTORS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{doctor_id}|{name}|{specialty}|{available_days}|{start_time}|{end_time}\n")

    log_action(f"DOCTOR_ADD: New doctor added with ID {doctor_id}, Name: {name}, Specialty: {specialty}")
    print(f"Doctor added successfully! Doctor ID: {doctor_id}")


def view_doctor_schedule():
    """
    View a specific doctor's appointment schedule.
    """
    print("\n--- View Doctor's Schedule ---")
    doctor_id_str = input("Enter Doctor ID: ").strip()
    if not doctor_id_str.isdigit():
        print("Error: Doctor ID must be a number.")
        return

    doctor_id = int(doctor_id_str)
    found_doctor = False
    doctor_name = ""

    try:
        with open(DOCTORS_FILE, 'r', encoding='utf-8') as doc_f:
            for line in doc_f:
                stripped_line = line.strip()
                if not stripped_line:  # Skip empty lines
                    continue

                parts = stripped_line.split('|')
                # *** FIX IS HERE ***: Check if part[0] is a digit before converting
                if len(parts) > 0 and parts[0].isdigit() and int(parts[0]) == doctor_id:
                    doctor_name = parts[1]
                    found_doctor = True
                    break

        if not found_doctor:
            print(f"No doctor found with ID {doctor_id}.")
            return

        print(f"\n--- Schedule for Doctor: {doctor_name} ---")

        with open(APPOINTMENTS_FILE, 'r', encoding='utf-8') as app_f, \
                open(PATIENTS_FILE, 'r', encoding='utf-8') as pat_f:

            appointments = []
            for line in app_f:
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                parts = stripped_line.split('|')
                if len(parts) == 6 and parts[2] == str(doctor_id) and parts[5] == 'Confirmed':
                    appointments.append(stripped_line)

            patients_data = {}
            for line in pat_f:
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                parts = stripped_line.split('|')
                if len(parts) > 1:
                    patients_data[parts[0]] = parts

            if not appointments:
                print("No booked appointments for this doctor.")
                return

            for app in appointments:
                parts = app.split('|')
                pat_id = parts[1]
                date = parts[3]
                time = parts[4]
                patient_info = patients_data.get(pat_id)
                patient_name = patient_info[1] if patient_info and len(patient_info) > 1 else "Unknown Patient"
                print(f"Date: {date}, Time: {time}, Patient Name: {patient_name}")

    except FileNotFoundError:
        print("Error: Cannot access data files.")
    except (ValueError, IndexError) as e:
        print(f"An error occurred while processing data files: {e}")


def backup_system_data():
    """
    Create a backup of all data files in the backups folder.
    """
    print("\n--- Starting Backup ---")
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_subdir = os.path.join(BACKUP_DIR, f'backup_{timestamp}')
        os.makedirs(backup_subdir)

        shutil.copy(DOCTORS_FILE, backup_subdir)
        shutil.copy(PATIENTS_FILE, backup_subdir)
        shutil.copy(APPOINTMENTS_FILE, backup_subdir)

        log_action(f"BACKUP: System data backed up to '{backup_subdir}'")
        print(f"Backup created successfully in: {backup_subdir}")
    except Exception as e:
        log_action(f"BACKUP_ERROR: Failed to create backup. Error: {e}")
        print(f"Backup failed. Error: {e}")


# --- Menus ---

def patient_menu():
    """
    Patient menu options.
    """
    while True:
        print("\n--- Patient Services Menu ---")
        print("1. Register as a New Patient")
        print("2. Book Appointment")
        print("3. View My Appointments")
        print("4. Cancel Appointment")
        print("5. Return to Main Menu")
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            register_new_patient()
        elif choice == '2':
            book_new_appointment()
        elif choice == '3':
            view_appointment_history()
        elif choice == '4':
            cancel_appointment()
        elif choice == '5':
            break
        else:
            print("Invalid choice, please try again.")
        input("\nPress Enter to continue...")


def admin_menu():
    """
    Admin menu options.
    """
    while True:
        print("\n--- Admin Services Menu ---")
        print("1. Add New Doctor")
        print("2. View Doctor's Schedule")
        print("3. Backup System Data")
        print("4. Return to Main Menu")
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            add_new_doctor()
        elif choice == '2':
            view_doctor_schedule()
        elif choice == '3':
            backup_system_data()
        elif choice == '4':
            break
        else:
            print("Invalid choice, please try again.")
        input("\nPress Enter to continue...")


def main_menu():
    """
    Main menu for selecting role (Patient or Admin).
    """
    check_files()
    log_action("SYSTEM_START: Application started.")

    while True:
        print("\n========================================")
        print("  Outpatient Clinic Booking System")
        print("========================================")
        print("Choose your role:")
        print("1. Patient")
        print("2. Admin")
        print("3. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            patient_menu()
        elif choice == '2':
            admin_menu()
        elif choice == '3':
            log_action("SYSTEM_EXIT: Application closed.")
            print("Thank you for using the system. Goodbye!")
            break
        else:
            print("Invalid choice, please enter 1, 2, or 3.")


if __name__ == "__main__":
    main_menu()