import subprocess
import os

def run_script(script_name):
    script_path = os.path.join('Scripts', script_name)
    try:
        subprocess.run(['python', script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the script: {e}")
    except FileNotFoundError:
        print(f"The script {script_name} was not found.")

def main():
    print("What kind of item are we working with?")
    print("1.   Tile")
    print("2.   Tool")
    choice = input("Enter the number of the script you want to run: ")

    if choice == '1':
        run_script('create-tile-v4.py')
    elif choice == '2':
        run_script('create-tool.py')
    else:
        print("Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    main()
