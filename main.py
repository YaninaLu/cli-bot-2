from collections import UserDict
from typing import Tuple, Callable, List, Any
from re import match


class CliApp:
    """
    A class that is responsible for communicating with the user.

    It takes input from the user, parses it and sends it to the AssistantBot class. Also, it outputs the result that
    returns from the bot and terminates the app when the user inputs one of the stop words.
    """

    def run(self):
        """
        Waits for the user input in an infinite loop. Terminates when one of the stop words is given.

        :return: result of running the command by the bot
        """
        bot = AssistantBot()
        while True:
            command, args = self.parse_command(input().lower())
            if command in ["good bye", "close", "exit"]:
                print("Good bye!")
                break
            else:
                result = bot.handle(command, args)
                if result:
                    print(result)

    @staticmethod
    def parse_command(user_input: str) -> Tuple[str, list[str]]:
        """
        Parses the string input into a tuple of command and arguments.

        :param user_input: a string that user provides
        :return: tuple(command, *args)
        """
        user_input = user_input.split()
        if len(user_input) == 0:
            raise ValueError()
        command = user_input[0]
        args = user_input[1:]
        return command, args


class AssistantBot:
    """
    A class that is responsible for identifying and calling functions that correspond to the given command.

    It stores commands and corresponding functions in a dictionary and calls these functions with the given arguments.
    It also catches exceptions on the domain level. When the user calls commands connected with managing the adressbook,
    bot sends them to the PhoneBook class.
    """
    def __init__(self):
        self.commands = {
            "hello": self.hello,
            "add": self.add,
            "delete": self.delete,
            "change": self.change,
            "phone": self.show,
            "show": self.show,
            "save": self.save_name
        }
        self.addressbook = AddressBook()

    @staticmethod
    def input_error(func: Callable) -> Callable[[tuple[Any, ...]], str | Any]:
        """
        Catches exceptions on the domain level (i.e. mistakes that prevent functions to fulfil their promises).

        :param func: function to execute
        :return: inner function that checks for exceptions when the function to execute is run
        """

        def exception_handler(*args, **kwargs):

            try:
                result = func(*args, **kwargs)
            except TypeError as err:
                return f"Invalid input, some info is missing: {err}"
            except KeyError as err:
                return f"Sorry, no such command: {err}"
            except ValueError as err:
                return f"ValueError: {err}"
            else:
                return result

        return exception_handler

    @input_error
    def handle(self, command: str, args: List[str]) -> str:
        """
        An entry point for the commands given by the user. It takes a corresponding function from the dictionary and
        calls its instance with the given arguments.

        :param command: command given by the user
        :param args: arguments to call the function with
        :return: function call with the given arguments
        """
        handler = self.commands[command]
        return handler(*args)

    @staticmethod
    @input_error
    def hello():
        """
        Returns a greeting to the 'hello' command.

        :return: greeting string
        """
        return "How can I help you?"

    @input_error
    def add(self, name: str, phone=None) -> None:
        """
        Calls a function that adds the given phone number to the addressbook.

        :param name: name of the person to add
        :param phone: phone of the person to add
        """
        if name in self.addressbook.data:
            record = self.addressbook.data[name]
            phone_object = Phone()
            phone_object.save_phone(phone)
            return record.add_phone(phone_object)
        else:
            record = Record()
            record.save_name(name)
            if phone:
                phone_object = Phone()
                phone_object.save_phone(phone)
                record.add_phone(phone_object)
            return self.addressbook.add_record(record)


    @input_error
    def change(self, name: str, new_phone: str) -> None:
        """
        Calls a function that changes the phone number of the given person.

        :param new_phone: a new phone number
        :param phone_to_change: an old phone number that user wants to change
        :param name: name that has to be already present in the addressbook
        """
        record = self.addressbook.data[name]
        phone_object = Phone()
        phone_object.save_phone(new_phone)
        return record.change_phone(phone_object)

    @input_error
    def show(self, name: str) -> str:
        """
        Calls a function that shows the phone number of the given person.

        :param name: name of a person or 'all' if the user wants all the addressbook to be printed
        :return: phone number or the whole addressbook
        """
        return self.addressbook.show_phone(name)

    def delete(self, name, phone):
        record = self.addressbook.data[name]
        return record.delete_phone(phone)

    def save_name(self, name):
        record = Record()
        record.save_name(name)
        return self.addressbook.add_record(record)


class AddressBook(UserDict):
    def add_record(self, record):
        if record.name.value not in self.data:
            self.data[record.name.value] = record
        else:
            raise ValueError(
                "This name is already in your phonebook. If you want to change the phone number, type 'change'.")

    def show_phone(self, name):
        """
        Shows the phone number of a given person. If 'all' was given as an argument it returns the whole phonebook.

        :param name: name to show or 'all'
        :return: phone number or phonebook as a string
        """
        if name == "all":
            if self.data:
                return str(self)
            else:
                return "You do not have any contacts yet."
        else:
            return str(self.data[name])

    def __str__(self):
        result = ""
        for name, record in self.data.items():
            result += str(record)
        return result


class Record:
    def __init__(self):
        self.name = None
        self.phones = []

    def save_name(self, name):
        self.name = Name(name)

    def add_phone(self, phone):
        self.phones.append(phone)

    def delete_phone(self, phone):
        for phone_object in self.phones:
            if phone_object.phone == phone:
                self.phones.remove(phone_object)

    def change_phone(self, new_phone):
        self.phones.clear()
        self.phones.append(new_phone)

    def __str__(self):
        phones = ", ".join(map(lambda phone: str(phone), self.phones))
        return f"Name: {self.name}, phones: {phones}\n"


class Field:
    def __init__(self):
        self.value = None


class Name(Field):
    def __init__(self, name):
        super().__init__()
        self.value = name

    def __str__(self):
        return f"{self.value}"

class Phone(Field):
    def __init__(self):
        super().__init__()
        self.phone = None

    def verify_phone(self, phone):
        """
        Checks if the phone number is valid. Throws exception if it's not valid.

        :param phone: phone number as a string
        :return: exception if it doesn't match the needed pattern
        """
        if not match(r"(\+?\d{12}|\d{10})", phone):
            raise ValueError("Invalid phone format")
        return True

    def save_phone(self, phone):
        if self.verify_phone(phone):
            self.phone = phone
        else:
            raise ValueError("Invalid phone format. Try +123456789012 or 1234567890.")

    def __str__(self):
        return f"{self.phone}"


def main():
    CliApp().run()


if __name__ == "__main__":
    main()
