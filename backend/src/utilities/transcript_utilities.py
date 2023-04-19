import re
import logging
from src.database.database_crud import get_course_title
from typing import Dict, List
from .course_utilities import Course
from sqlalchemy.orm import Session

class Transcript:
    def __init__(self, student_surname, student_given_name, student_number, courses):
        self.student_surname = student_surname
        self.student_given_name = student_given_name
        self.student_number = student_number
        self.courses = courses

    def __str__(self):
        s = "==================================================================\n"
        s += "Student Name: {} {} Student Number: {}\n" \
            .format(self.student_given_name, self.student_surname, self.student_number)
        for k in self.courses:
            s += f"=== {k} ===\n"
            for v in self.courses[k]:
                s += f"{v}\n"
        
        s += "==================================================================\n"
        return s


    def add_course(self, session: str, course: Course):
        if session in self.courses:
            self.courses[session].append(course)
        else:
            self.courses[session] = [course]

class TranscriptParser:
    def __init__(self, db: Session, data: List[str]):
        self.data: List[str] = data
        self.db = db

    def parse(self) -> Transcript:
        student_data = self.parse_student_data()
        student_surname = student_data["student_surname"]
        student_given_name = student_data["student_given_name"]
        student_number = student_data["student_number"]
        courses = self.parse_course_data()
        return Transcript(student_surname, student_given_name, student_number, courses)

    def parse_student_data(self) -> Dict[str, str]:
        student_data = {}

        # regex explanation
        # Name:: This part of the pattern matches the exact string "Name:".
        # (.*),: The (.*) part is a capturing group that matches any sequence of characters 
        #       (. matches any character, and * means to match the preceding character zero or more times). 
        #       The .* is followed by a comma which matches the comma separating the student's surname and given name. 
        #       The (.*) in parentheses captures the matched surname.
        # \s+: This part of the pattern matches one or more whitespace characters. 
        #       \s matches any whitespace character (including spaces, tabs, and newlines), 
        #       and + means to match the preceding character one or more times.
        # (.*): Another capturing group, similar to the one described in surname group. 
        #       This one captures the student's given name.
        # \s+#:: This part matches one or more whitespace characters followed by the exact string "#:".
        # (\d+): This part is another capturing group that matches one or more digits (0-9). 
        #        \d matches any digit, and + means to match the preceding character one or more times. The (\d+) in parentheses captures the matched student number.
        student_data_pattern = re.compile(r"Name:(.*),\s+(.*)\s+#:(\d+)")

        for d in self.data:
            match = student_data_pattern.search(d)
            if match:
                student_data["student_surname"] = match.group(1).strip()
                student_data["student_given_name"] = match.group(2).strip()
                student_data["student_number"] = match.group(3).strip()
                break
        
        if not any(student_data):
            logging.error("Failed to retrieve student data.")
            # TODO: Think about how to handle this case

        return student_data

    def parse_course_data(self) -> Dict[str, List[Course]]:
        courses = {}

        lines_list = self.split_extracted_data_to_lines()

        # This pattern matches with a line that contains course grade info.
        # If the lins contains course grade info, it starts with course code
        # e.b. CPEN 221, WRDS 150B
        course_info_line_pattern = r"^[A-Z]{4} \d{3}[A-Z]?"

        for line in lines_list:
            # TODO: Consider a better approach
            if re.match(course_info_line_pattern, line):
                words: List[str] = line.split()
                word_count: int = len(words)

                course: Course = None

                match word_count:
                    case 11:
                        course = self.create_non_pass_fail_course(words)
                    case 10:
                        course = self.create_pass_fail_course_with_term(words)
                    case 9:
                        course = self.create_pass_fail_course_without_term(words)
                    case 8:
                        course = self.create_withdraw_course(words)
                    case 6:
                        course = self.create_in_progress_course(words)
                    case _:
                        course = None
                        logging.error(f"Failed to parse course data. Please check transcript_utilities:parse_course_data. {line}")

                if course:
                    courses.setdefault(course.session, []).append(course)                

        return courses
    
    # TODO: Refactor creater functions and make it cleaner
    def create_non_pass_fail_course(self, words: List[str]):
        subject = words[0]
        code = words[1] 
        section = words[2]
        num_grade = words[3]
        # To log error in case PDF extractor failed to extract letter grade properly (e.g. Ac -or- A*)
        if len(words[4]) == 2 and words[4][1] != "+" and words[4][1] != "-":
            logging.error(f"Failed to parse course letter grade. Please check transcript_utilities:create_non_pass_fail_course. {words[4]}")
        letter_grade = words[4]
        session = words[5]
        term = words[6]
        year = words[8]
        credit = words[9]
        average = words[10]
        standing = ""
        title = get_course_title(db=self.db, subject=subject, code=code)
        return Course(session=session, section=section, term=term, 
                      subject=subject, code=code, credit=credit, 
                      title=title, num_grade=num_grade, letter_grade=letter_grade, 
                      average=average, year=year, standing=standing)

    def create_pass_fail_course_with_term(self, words: List[str]):
        subject = words[0]
        code = words[1] 
        section = words[2]
        session = words[3]
        term = words[4]
        year = words[6]
        credit = words[7]
        standing = words[9]
        average = "n/a"
        num_grade = ""
        letter_grade = ""
        title = get_course_title(db=self.db, subject=subject, code=code)
        return Course(session=session, section=section, term=term, 
                      subject=subject, code=code, credit=credit, 
                      title=title, num_grade=num_grade, letter_grade=letter_grade, 
                      average=average, year=year, standing=standing)

    def create_pass_fail_course_without_term(self, words: List[str]):
        subject = words[0]
        code = words[1] 
        section = words[2]
        session = words[3]
        year = words[5]
        credit = words[6]
        standing = words[8]
        average = "n/a"
        term = ""
        num_grade = ""
        letter_grade = ""
        title = get_course_title(db=self.db, subject=subject, code=code)
        return Course(session=session, section=section, term=term, 
                      subject=subject, code=code, credit=credit, 
                      title=title, num_grade=num_grade, letter_grade=letter_grade, 
                      average=average, year=year, standing=standing)

    def create_in_progress_course(self, words: List[str]):
        subject = words[0]
        code = words[1] 
        section = words[2]
        session = words[3]
        year = words[5]
        title = get_course_title(db=self.db, subject=subject, code=code)
        standing= "CIP"
        credit = ""
        average = ""
        term= ""
        num_grade = ""
        letter_grade = ""
        return Course(session=session, section=section, term=term, 
                      subject=subject, code=code, credit=credit, 
                      title=title, num_grade=num_grade, letter_grade=letter_grade, 
                      average=average, year=year, standing=standing)

    def create_withdraw_course(self, words: List[str]):
        subject = words[0]
        code = words[1] 
        section = words[2]
        session = words[3]
        term = words[4]
        year = words[6]
        standing = words[7]
        title = get_course_title(db=self.db, subject=subject, code=code)
        credit = ""
        num_grade = ""
        letter_grade = ""
        average = ""
        return Course(session=session, section=section, term=term, 
                      subject=subject, code=code, credit=credit, 
                      title=title, num_grade=num_grade, letter_grade=letter_grade, 
                      average=average, year=year, standing=standing)

    def split_extracted_data_to_lines(self) -> List[str]:
        lines_list: List[str] = []
        for page in self.data:
            lines = page.split("\n")
            for line in lines:
                lines_list.append(line)

        return lines_list
       
