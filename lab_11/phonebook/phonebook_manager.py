import psycopg2
import csv
import os
import sys
from config import DB_SETTINGS, CSV_HEADER

def connect_db():
    """ Connects to the PostgreSQL database. Returns connection object or None. """
    conn = None
    try:
        conn = psycopg2.connect(**DB_SETTINGS)
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error connecting to database: {error}")
        return None
def print_query_results(results):
    """ Formats and prints a list of contact rows. """
    if results:
        print("\n--- Results ---")
        print(f"{'ID':<5} {'First Name':<15} {'Last Name':<15} {'Phone Number':<20}")
        print("-" * 55)
        for row in results:
            print(f"{row[0]:<5} {row[1]:<15} {row[2]:<15} {row[3]:<20}")
        print("-" * 55)
        print(f"Found {len(results)} contact(s).")
    else:
        print("\nNo results to display.")
def create_phonebook_table():
    """ Creates the 'contacts' table if it doesn't exist. """
    sql_command = """
        CREATE TABLE IF NOT EXISTS contacts (
            contact_id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            phone_number VARCHAR(20) NOT NULL UNIQUE
        );
    """
    conn = connect_db()
    if not conn:
        return

    try:
        with conn, conn.cursor() as cur:
            cur.execute(sql_command)
            print("Table 'contacts' checked/created successfully.")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error creating table: {error}")
    finally:
        if conn:
            conn.close()

def add_contact():
    """ Gets user input and adds a single contact to the database. """
    try:
        first_name = input("Enter first name: ").strip()
        last_name = input("Enter last name: ").strip()
        phone_number = input("Enter phone number: ").strip()

        if not first_name or not last_name or not phone_number:
            print("Error: First name, last name, and phone number cannot be empty.")
            return

        sql = "INSERT INTO contacts (first_name, last_name, phone_number) VALUES (%s, %s, %s) RETURNING contact_id;"
        conn = connect_db()
        if not conn:
            return

        try:
            with conn, conn.cursor() as cur:
                cur.execute(sql, (first_name, last_name, phone_number))
                new_id = cur.fetchone()[0]
                print(f"Contact '{first_name} {last_name}' added successfully with ID: {new_id}.")
        except psycopg2.IntegrityError as e:
             if "contacts_phone_number_key" in str(e):
                 print(f"Error: Phone number '{phone_number}' already exists.")
             else:
                 print(f"Database integrity error: {e}")
             conn.rollback()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error adding contact: {error}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

    except (KeyboardInterrupt, EOFError):
        print("\nAdd contact cancelled.")

def add_contacts_from_csv():
    """ Reads contacts from a CSV file and inserts them into the database. """
    try:
        file_path = input("Enter path to CSV file: ").strip()
        if not os.path.exists(file_path):
            print(f"Error: File not found at '{file_path}'")
            return

        contacts_to_add = []
        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                try:
                    header = next(reader)
                    if header != CSV_HEADER:
                        print(f"Warning: CSV header mismatch. Expected {CSV_HEADER}, got {header}.")
                except StopIteration:
                     print("Error: CSV file is empty or has no header.")
                     return

                for row_num, row in enumerate(reader, start=2):
                     if len(row) == 3:
                         first, last, phone = [col.strip() for col in row]
                         if first and last and phone: # Basic check for empty fields
                            contacts_to_add.append((first, last, phone))
                         else:
                            print(f"Warning: Skipping row {row_num} in CSV - contains empty fields.")
                     else:
                         print(f"Warning: Skipping row {row_num} in CSV - incorrect column count.")

        except Exception as e:
             print(f"Error reading CSV file: {e}")
             return

        if not contacts_to_add:
            print("No valid contacts found in CSV to add.")
            return

        conn = connect_db()
        if not conn:
            return

        inserted_count = 0
        failed_count = 0
        sql = "INSERT INTO contacts (first_name, last_name, phone_number) VALUES (%s, %s, %s);"

        try:
            with conn, conn.cursor() as cur:
                print(f"Attempting to insert {len(contacts_to_add)} contacts from CSV...")
                for contact in contacts_to_add:
                    try:
                        cur.execute(sql, contact)
                        inserted_count += 1
                    except psycopg2.IntegrityError as e:
                        print(f"  Skipping '{contact[0]} {contact[1]}' - Phone '{contact[2]}' likely already exists.")
                        failed_count += 1
                    except (Exception, psycopg2.DatabaseError) as error:
                         print(f"  Error inserting '{contact[0]} {contact[1]}': {error}")
                         failed_count += 1

            print(f"\nCSV Import Summary:")
            print(f" Successfully inserted: {inserted_count}")
            print(f" Failed/Skipped rows: {failed_count}")

        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error during bulk insert transaction: {error}")
        finally:
            if conn:
                conn.close()

    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled.")


def update_contact():
    """ Updates a contact's details based on their phone number. """
    try:
        phone_to_update = input("Enter the CURRENT phone number of the contact to change: ").strip()
        if not phone_to_update:
            print("Error: Phone number cannot be empty.")
            return

        print("\nWhat do you want to update?")
        print(" 1. First Name")
        print(" 2. Last Name")
        print(" 3. Phone Number")
        choice = input("Enter choice (1-3): ").strip()

        column_to_update = ""
        if choice == '1':
            column_to_update = "first_name"
        elif choice == '2':
            column_to_update = "last_name"
        elif choice == '3':
            column_to_update = "phone_number"
        else:
            print("Invalid choice.")
            return

        new_value = input(f"Enter the new value for {column_to_update}: ").strip()
        if not new_value:
            print("Error: The new value cannot be empty.")
            return

        if column_to_update not in ["first_name", "last_name", "phone_number"]:
             print("Internal Error: Invalid column selected.")
             return

        sql = f"UPDATE contacts SET {column_to_update} = %s WHERE phone_number = %s;"

        conn = connect_db()
        if not conn:
            return

        try:
            with conn, conn.cursor() as cur:
                cur.execute(sql, (new_value, phone_to_update))
                if cur.rowcount > 0:
                    print(f"Contact with phone '{phone_to_update}' updated successfully.")
                else:
                    print(f"No contact found with phone number '{phone_to_update}'. No changes made.")
        except psycopg2.IntegrityError as e:
             if "contacts_phone_number_key" in str(e):
                 print(f"Error: Cannot update phone number to '{new_value}', as it already exists for another contact.")
             else:
                  print(f"Database integrity error: {e}")
             conn.rollback()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error updating contact: {error}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

    except (KeyboardInterrupt, EOFError):
        print("\nUpdate cancelled.")

def find_contacts():
    """ Searches for contacts based on a pattern in name or phone number. """
    try:
        pattern = input("Enter search text (part of first name, last name, or phone): ").strip()
        if not pattern:
            print("Search text cannot be empty.")
            return

        sql = """
            SELECT contact_id, first_name, last_name, phone_number
            FROM contacts
            WHERE first_name ILIKE %s OR last_name ILIKE %s OR phone_number LIKE %s
            ORDER BY last_name, first_name;
        """
        search_pattern = f"%{pattern}%"

        conn = connect_db()
        if not conn:
            return

        results = []
        try:
            with conn, conn.cursor() as cur:
                cur.execute(sql, (search_pattern, search_pattern, search_pattern))
                results = cur.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error searching contacts: {error}")
        finally:
            if conn:
                conn.close()

        print_query_results(results)

    except (KeyboardInterrupt, EOFError):
        print("\nSearch cancelled.")


def list_contacts_paginated():
    """ Lists contacts from the database page by page. """
    try:
        try:
            limit = int(input("How many contacts per page? (e.g., 5): ").strip())
            offset = int(input("Which record to start from? (e.g., 0 for first page): ").strip())
            if limit <= 0 or offset < 0:
                print("Error: Records per page must be positive, starting record must be 0 or more.")
                return
        except ValueError:
            print("Error: Please enter valid numbers for page size and starting record.")
            return

        sql = """
            SELECT contact_id, first_name, last_name, phone_number
            FROM contacts
            ORDER BY last_name, first_name
            LIMIT %s OFFSET %s;
        """
        conn = connect_db()
        if not conn:
            return

        results = []
        try:
            with conn, conn.cursor() as cur:
                cur.execute(sql, (limit, offset))
                results = cur.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error listing contacts: {error}")
        finally:
            if conn:
                conn.close()

        if results:
             print(f"\n--- Showing Contacts {offset + 1} to {offset + len(results)} ---")
             print_query_results(results)
        else:
             print("\nNo contacts found for this page.")


    except (KeyboardInterrupt, EOFError):
        print("\nListing cancelled.")

def delete_contact():
    """ Deletes a contact based on their phone number. """
    try:
        phone_to_delete = input("Enter the exact phone number of the contact to delete: ").strip()
        if not phone_to_delete:
            print("Error: Phone number cannot be empty.")
            return

        confirm = input(f"Are you absolutely sure you want to delete the contact with phone '{phone_to_delete}'? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Deletion cancelled.")
            return

        sql = "DELETE FROM contacts WHERE phone_number = %s;"
        conn = connect_db()
        if not conn:
            return

        try:
            with conn, conn.cursor() as cur:
                cur.execute(sql, (phone_to_delete,))
                if cur.rowcount > 0:
                    print(f"Contact with phone '{phone_to_delete}' deleted successfully.")
                else:
                    print(f"No contact found with phone '{phone_to_delete}'.")
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error deleting contact: {error}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

    except (KeyboardInterrupt, EOFError):
        print("\nDeletion cancelled.")

def print_menu():
    print("\n--- Simple PhoneBook Menu ---")
    print(" 1. Add New Contact")
    print(" 2. Add Contacts from CSV File")
    print(" 3. Update Existing Contact (by Phone)")
    print(" 4. Find Contacts (by Name/Phone fragment)")
    print(" 5. List Contacts (Paginated)")
    print(" 6. Delete Contact (by Phone)")
    print(" 7. Create Contacts Table (Run if needed)")
    print(" 0. Exit")
    print("-----------------------------")

def main():
    while True:
        print_menu()
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            add_contact()
        elif choice == '2':
            add_contacts_from_csv()
        elif choice == '3':
            update_contact()
        elif choice == '4':
            find_contacts()
        elif choice == '5':
            list_contacts_paginated()
        elif choice == '6':
            delete_contact()
        elif choice == '7':
             confirm = input("Attempt to create 'contacts' table if it doesn't exist? (yes/no): ").strip().lower()
             if confirm == 'yes':
                 create_phonebook_table()
             else:
                 print("Table creation cancelled.")
        elif choice == '0':
            print("Exiting PhoneBook. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    print("Welcome to the Simple PhoneBook!")
    initial_conn = connect_db()
    if initial_conn:
         initial_conn.close()
         main()
    else:
         print("Could not connect to the database on startup. Exiting.")
         sys.exit(1)