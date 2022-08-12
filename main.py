from collections import UserDict
from typing import Tuple, Callable, List, Any
from re import match


class CliApp:
    """
    Communicates with the user.

    Takes input from the user, parses it and sends it to the assistant bot. Responds with the result
    from the bot. Terminates the app when the user inputs one of the stop words.
    """

    def run(self):
        """
        Waits for the user input in an infinite loop. Terminates when one of the stop words is given.

        :return: result of running the command by the bot
        """
        bot = AssistantBot()
        while True:
            command, args = self.parse_command(input())
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
        Parses the input into a command and zero or more arguments.

        :param user_input: a string that user provides
        :return: tuple(command, *args)
        """
        if len(user_input) == 0:
            raise ValueError()
        user_input = user_input.split()
        command = user_input[0].lower()
        args = user_input[1:]
        return command, args


class AssistantBot:
    """
    Assists a user with managing their address book (adding, deleting, changing, displaying entries).
    """

    def __init__(self):
        self.commands = {
            "hello": self.hello,
            "add": self.add,
            "delete": self.delete,
            "change": self.change,
            "phone": self.show,
            "show": self.show
        }
        self.addressbook = AddressBook()

    @staticmethod
    def input_error(func: Callable) -> Callable[[tuple[Any, ...]], str | Any]:
        """
        A decorator that catches the domain-level exceptions and returns human-readable error message.
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
        Calls the command and returns a result of it.

        :param command: command given by the user
        :param args: arguments to call the command with
        :return: command to execute with the arguments
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
    def add(self, name: str, phone: None | str = None) -> None:
        """
        Calls and returns a function that adds the given phone number to the addressbook.

        :param name: name of the person to add, compulsory field
        :param phone: phone of the person to add, optional field
        """
        if name in self.addressbook.data:
            record = self.addressbook.data[name]
            return record.add_phone(phone)
        else:
            record = Record(name)
            if phone:
                record.add_phone(phone)
            return self.addressbook.add_record(record)

    @input_error
    def change(self, name: str, old_phone: str, new_phone: str) -> None:
        """
        Calls and returns a function that replaces the phone number of the given person.

        :param new_phone: a new phone number
        :param old_phone: a number to delete
        :param name: a name that has to be already present in the address book
        """
        record = self.addressbook.data[name]
        record.delete_phone(old_phone)
        return record.add_phone(new_phone)

    @input_error
    def show(self, name: str) -> str:
        """
        Returns the phone number of the given person.

        :param name: name of a person or 'all' if the user wants all the address book to be printed
        :return: phone number or the whole addressbook
        """
        return self.addressbook.show_phone(name)

    def delete(self, name: str, phone: str) -> None:
        """
        Calls and returns a function that deletes the given phone number from the record of the given person.

        :param name: whose phone the user wants to delete
        :param phone: a phone to delete
        """
        record = self.addressbook.data[name]
        return record.delete_phone(phone)


class Field:
    """
    The base class for the fields of the Record class.
    """

    def __init__(self):
        self.value = None

    def __str__(self):
        return f"{self.value}"

    def __hash__(self) -> int:
        return self.value.__hash__()

    def __eq__(self, o: object) -> bool:
        return self.value == o


class Name(Field):
    """
    A name of a person in an address book.
    """

    def __init__(self, name: str):
        super().__init__()
        self.value = name


class Phone(Field):
    """
    A phone number of a person in an address book.
    """

    def __init__(self, phone: str):
        super().__init__()
        self.__verify(phone)
        self.value = phone

    @staticmethod
    def __verify(phone: str):
        """
        Checks if the phone number is valid. Throws an exception if it's not valid.

        :param phone: phone number as a string
        :return: exception if it doesn't match the needed pattern
        """
        if not match(r"(\+?\d{12}|\d{10})", phone):
            raise ValueError("Invalid phone format. Try +123456789012 or 1234567890.")


class Record:
    """
    A record about a person in an address book. Name field is compulsory, while phones field is optional and can
    be omitted.
    """

    def __init__(self, name: str):
        if not name:
            raise ValueError("The record must have a name.")
        self.name = Name(name)
        self.phones = []

    def add_phone(self, phone: str) -> None:
        """
        Adds a phone to the record.

        :param phone: a phone number
        """
        phone_object = Phone(phone)
        self.phones.append(phone_object)

    def delete_phone(self, phone: str) -> None:
        """
        Deletes a phone from the record.

        :param phone: a phone number to delete
        """

        phone = self.find_phone(phone)
        if phone:
            self.phones.remove(phone)
        else:
            raise ValueError("The given phone is not in a list.")

    def find_phone(self, phone: str) -> Phone:
        """
        Finds and returns a phone from the phone list.

        :param phone: phone to search
        :return: an entry in a phone list corresponding to this phone
        """
        for phone_object in self.phones:
            if phone_object.value == phone:
                return phone_object

    def __str__(self):
        phones = ", ".join(map(lambda phone: str(phone), self.phones))
        return f"Name: {self.name}, phones: {phones}\n"


class AddressBook(UserDict):
    """
    An address book.
    """

    def add_record(self, record: Record) -> None:
        """
        Adds a new record to the address book. If the name is already present in the book, it either offers to change
        the phone corresponding to it or add a new phone number to the record.

        :param record: a record to add
        """
        if record.name not in self.data:
            self.data[record.name] = record
        else:
            raise ValueError(
                "This name is already in your phonebook. If you want to change the phone number, type 'change'."
                "If you want to add a phone number, type it after the name.")

    def show_phone(self, name: str) -> str:
        """
        Returns the phone number of a given person. If 'all' was given as an argument it returns the whole phonebook.

        :param name: name to show or 'all'
        :return: phone number or addressbook as a string
        """
        if name == "all":
            if self.data:
                return str(self)
            else:
                return "You do not have any contacts yet."
        else:
            if name in self.data:
                return str(self.data[name])
            else:
                return "You don't have a contact with this name in your address book."

    def __str__(self):
        result = ""
        for name, record in self.data.items():
            result += str(record)
        return result


if __name__ == "__main__":
    CliApp().run()
