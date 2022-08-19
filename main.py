from collections import UserDict
from typing import Tuple, Callable, List, Any
from re import match
from datetime import datetime


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
        try:
            while True:
                command, args = self.parse_command(input())
                if command in ["goodbye", "close", "exit"]:
                    print("Goodbye!")
                    break
                else:
                    result = bot.handle(command, args)
                    if result:
                        print(result)
        except Exception as err:
            print(err)

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
            "show": self.show,
            "help": self.help
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
    def help() -> str:
        """
        Displays the help message.
        :return:
        """

        return "To add a new person type: 'add name phone birthday'.\n" \
               "To add a phone to the existing record type: 'add name phone'.\n" \
               "To add a birthday to the existing record type: 'add name birthday'.\n" \
               "To delete a phone from a person's record type: 'delete name phone'.\n" \
               "To delete a person's record from the address book type: 'delete name'.\n" \
               "To change a person's phone type: 'change name old_phone new_phone'.\n" \
               "To see a particular phone type: 'show name'.\n" \
               "To see part of the address book type: 'show num_of_entries'.\n" \
               "To see the whole address book type: 'show all'.\n" \
               "Possible phone formats: +123456789011 or 123456789011 or 1234567890.\n" \
               "Possible birthday format: dd.mm.yyyy.\n"

    @staticmethod
    @input_error
    def hello():
        """
        Returns a greeting to the 'hello' command.

        :return: greeting string
        """

        return "How can I help you?"

    @input_error
    def add(self, *args) -> None:
        """
        Calls and returns a function that adds the given information about a person to the addressbook.
        """

        if len(args) == 3:

            name, phone, birthday = args
            record = Record(name)
            record.add_phone(phone)
            birthday_date = datetime.strptime(birthday, "%d.%m.%Y").date()
            record.add_birthday(birthday_date)
            return self.addressbook.add_record(record)

        elif len(args) == 2:

            if args[0] in self.addressbook:
                record = self.addressbook.data[args[0]]
            else:
                record = Record(args[0])
                self.addressbook.add_record(record)

            if Phone.is_valid(args[1]):
                phone = args[1]
                return record.add_phone(phone)
            elif match(r"\d{2}\.\d{2}\.\d{4}", args[1]):
                birthday = args[1]
                birthday_date = datetime.strptime(birthday, "%d.%m.%Y").date()
                return record.add_birthday(birthday_date)
            else:
                raise ValueError("The format of your entry isn't right. Type in 'help' to see possible formats.")

        elif len(args) == 1:

            record = Record(args[0])
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
        Returns the record of the given person as a human-readable message.

        :param name: name of a person, 'all' if the user wants all the address book to be printed, 'page' if the
        user wants to see the address book page by page
        :return: information about a person, the whole address book, one page of the address book
        """

        return self.addressbook.show_record(name)

    def delete(self, name: str, phone: str | None = None) -> None:
        """
        Calls and returns a function that deletes the given phone number from the record of the given person or the
        whole record.

        :param name: whose phone the user wants to delete
        :param phone: a phone to delete (optional)
        """

        if phone:
            record = self.addressbook.data[name]
            return record.delete_phone(phone)
        else:
            return self.addressbook.delete_record(name)


class Field:
    """
    The base class for the fields of the Record class.
    """

    def __init__(self, value):
        self._value = None
        self.value = value

    def __str__(self):
        return f"{self.value}"

    def __hash__(self) -> int:
        return self.value.__hash__()

    def __eq__(self, o: object) -> bool:
        return self.value == o

    @staticmethod
    def verify_value(value):
        pass

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self.verify_value(value)
        self._value = value


class Name(Field):
    """
    A name of a person in an address book.
    """

    def verify_value(self, value: str):
        """
        Verifies that name consists only of alphabetical characters. Raises exception if the name contains something
        besides latin letters.

        :param value: a name to check
        """

        if not match(r"\b[A-Za-z]+", value):
            raise ValueError("Name can contain only latin letters.")


class Phone(Field):
    """
    A phone number of a person in an address book.
    """

    @classmethod
    def is_valid(cls, value: str):
        return match(r"(\+?\d{12}|\d{10})", value)

    def verify_value(self, value: str):
        """
        Checks if the phone is given in a valid format. Raises exception if the phone doesn't match one of the formats.

        :param value: phone number
        """

        if not Phone.is_valid(value):
            raise ValueError("Invalid phone format. Try +123456789012 or 1234567890.")


class Birthday(Field):
    """
    Person's birthday date.
    """

    def verify_value(self, value: datetime.date):
        """
        Checks if the birthdate is not in the future. Raises exception if the date is in the future.

        :param value: datetime object
        """

        if value > datetime.now().date():
            raise ValueError("Birthday can't be in future.")


class Record:
    """
    A record about a person in an address book. Name field is compulsory, while phones and birthday fields are optional
    and can be omitted.
    """

    def __init__(self, name: str):
        if not name:
            raise ValueError("The record must have a name.")
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone: str) -> None:
        """
        Adds a phone to the record.

        :param phone: a phone number
        """

        phone_object = Phone(phone)
        self.phones.append(phone_object)

    def delete_phone(self, phone: str) -> None:
        """
        Deletes a phone from the record. Raises exception if there is no such phone in the record.

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

    def count_days_to_birthday(self) -> str:
        """
        Counts the days left to the birthdate of the given person.

        :return: a message that contains a number of days left or a reminder that a person has their birthday today
        """

        today = datetime.now().date()
        this_years_birthday = self.birthday.value.replace(year=today.year)

        if today < this_years_birthday:
            difference = this_years_birthday - today
            return f"there are {difference.days} days to this person's birthday"
        if today == this_years_birthday:
            return "Today is this person's birthday!"
        else:
            next_years_birthday = this_years_birthday.replace(year=this_years_birthday.year + 1)
            difference = next_years_birthday - today
            return f"there are {difference.days} days to this person's birthday"

    def add_birthday(self, birthday: datetime.date):
        """
        Adds a birthdate to the record.

        :param birthday: datetime object
        """

        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = ", ".join(map(lambda phone: str(phone), self.phones))
        if self.birthday:
            return f"Name: {self.name}, phones: {phones}, birthday: {self.birthday}, {self.count_days_to_birthday()}"
        else:
            return f"Name: {self.name}, phones: {phones}"


class AddressBook(UserDict):
    """
    An address book.
    """

    PAGE_SIZE = 2

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._paginator = None

    def add_record(self, record: Record):
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

    def show_record(self, name: str) -> str:
        """
        Returns the info of a given person. If 'all' was given as an argument it returns the whole phonebook. If 'page'
        was given as an argument is shows the next page.

        :param name: name to show, 'all' or 'page'
        :return: a phone number, an addressbook, a page
        """
        if name == "all":
            if self.data:
                result = ""
                for value in self.data.values():
                    result += str(value) + "\n"
                return result
            else:
                return "You do not have any contacts yet."
        elif name == "page":
            page_content = next(self.paginator(), None)
            if not page_content:
                self._paginator = None
                return "You reached the end of the address book. Call this command again."
            else:
                return "\n".join([str(r) for r in page_content])
        else:
            if name in self.data:
                return str(self.data[name])
            else:
                return "You don't have a contact with this name in your address book."

    def delete_record(self, name: str) -> None:
        """
        Deletes the record of a person from an address book. Raises exception if this person is not in an address book.

        :param name: name of a person to delete
        """

        if name in self.data:
            del self.data[name]
        else:
            raise KeyError("This person is not in your address book.")

    def paginator(self):
        if not self._paginator:
            self._paginator = self.iterator()
        return self._paginator

    def iterator(self):
        """
        Yields pages of two entries from the address book.

        :return: one page of the address book
        """

        page_start = 0
        while True:
            values = list(self.data.values())
            if page_start >= len(values):
                break
            if page_start + AddressBook.PAGE_SIZE > len(values):
                remaining = len(values) - page_start
                page_end = page_start + remaining
            else:
                page_end = page_start + AddressBook.PAGE_SIZE
            yield values[page_start:page_end]
            page_start = page_end

    def __str__(self):
        result = ""
        for record in self.data.values():
            result += str(record)
        return result


if __name__ == "__main__":
    CliApp().run()
