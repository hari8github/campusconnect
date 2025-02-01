import os
import spacy
import pymongo
from typing import Dict, List, Optional
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import io
import base64
from flask import send_file
import json

# Load environment variables
load_dotenv()

class StudentAcademicChatbot:
    def __init__(self):
        """Initialize the chatbot with hardcoded MongoDB connection and NLP model"""
        # Hardcoded connection details
        self.mongodb_uri = 'mongodb://localhost:27017/'
        self.database_name = 'admin'
        self.collection_name = 'CampusConnect'

        # Load spaCy NLP model
        self.nlp = spacy.load("en_core_web_sm")
        
        try:
            # Establish MongoDB Connection
            self.client = pymongo.MongoClient(self.mongodb_uri)
            self.db = self.client[self.database_name]
            self.students_collection = self.db[self.collection_name]
            
            # Verify connection
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB!")
        
        except pymongo.errors.ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise
        
        # Intent Mapping
        self.intent_patterns = {
        'overall_performance': [
        'performance', 'gpa', 'grades', 'academic standing', 
        'total performance', 'cumulative performance', 'cgpa'
        ],
        'course_details': [ 
        'course', 'courses', 'class', 'subject', 
        'enrolled courses', 'course information'
        ],
        'attendance': [
        'attendance', 'classes', 'present', 'absent', 
        'class participation', 'how many classes', 'attendance percentage'
        ],
        'semester_performance': [
        'semester', 'semester gpa', 'last semester', 
        'performance this semester'
        ],
        'current_semester': [
        'current semester', 'what semester am i in', 'which semester', 'semester'
        ],
        'credit_status': [
                'credits', 'total credits', 'remaining credits', 'credit requirements',
                'credits completed', 'credits left'
            ],
            'program_details': [
                'program', 'department', 'admission', 'admission year', 
                'enrollment details', 'department details'
            ],
            'performance_trend': [
                'trend', 'progress', 'performance trend', 'grade trend',
                'improvement', 'academic progress'
            ],
            'attendance_alert': [
                'attendance risk', 'attendance warning', 'low attendance',
                'attendance status', 'attendance requirement'
            ],
            'course_load': [
                'course load', 'credit load', 'workload', 
                'credits this semester', 'semester load'
            ]
    }

    def get_student_details(self, student_id1, student_id2):
        # Fetch data from database
        student_data1 = self.retrieve_student_data(student_id1)
        student_data2 = self.retrieve_student_data(student_id2)
        return student_data1, student_data2

    def compare_students(self, student_data1, student_data2):
        # Compare GPA
        gpa1 = student_data1['academic_details']['academic_performance']['cgpa']
        gpa2 = student_data2['academic_details']['academic_performance']['cgpa']
    
        # Compare Credits Completed
        credits1 = student_data1['academic_details']['credits_completed']
        credits2 = student_data2['academic_details']['credits_completed']
    
        # Compare Attendance Percentage
        attendance1 = student_data1['academic_details']['attendance_percentage']
        attendance2 = student_data2['academic_details']['attendance_percentage']
    
        # Prepare comparison data
        comparison_data = {
            'Student 1': {
                'GPA': gpa1,
                'Credits': credits1,
                'Attendance': attendance1
            },
            'Student 2': {
                'GPA': gpa2,
                'Credits': credits2,
                'Attendance': attendance2
            }
        }
    
        return comparison_data

    def sort_students_by(self, data, sort_key, ascending=True):
       """Sort students data by specified key"""
       if not data:
        return []
        
       return sorted(data, key=lambda x: x[sort_key], reverse=not ascending)

    def get_sorted_common_details(self, sort_by='cgpa', ascending=True):
         """Get sorted common details"""
         data = self.get_common_details()
         if data:
            return self.sort_students_by(data, sort_by, ascending)
         return None

    def handle_common_details_query(self):
     """Comprehensive method to retrieve common student details"""
     try:
        # Retrieve student data from mock_dept_data.json
        with open('mock_dept_data.json', 'r') as file:
            data = json.load(file)
        
        # Extract student details
        students = []
        for entry in data:
            if 'students' in entry:
                for student_id, student_info in entry['students'].items():
                    academic_details = student_info.get('academic_details', {})
                    enrollment = academic_details.get('enrollment', {})
                    performance = academic_details.get('academic_performance', {})
                    attendance = academic_details.get('attendance', {})
                    
                    student_data = {
                        'name': f"Student {student_id.split('ST')[1]}",
                        'student_id': student_id,
                        'cgpa': performance.get('cgpa', 0),
                        'attendance': attendance.get('percentage', 0),
                        'credits_completed': len(academic_details.get('courses', [])),
                        'department': enrollment.get('department', 'Unknown')
                    }
                    students.append(student_data)
        
        return students

     except FileNotFoundError:
        print("Error: mock_dept_data.json file not found.")
        return []
     except json.JSONDecodeError:
        print("Error: mock_dept_data.json contains invalid JSON.")
        return []
     except Exception as e:
        print(f"Error in handle_common_details_query: {e}")
        return []

    def retrieve_student_data(self, student_id: str) -> Optional[Dict]:
        """
        Retrieve student data from MongoDB.
        Args:
            student_id (str): Student's unique identifier.
        Returns:
            Dict containing student's academic information or None.
        """
        try:
            # Query to find the student under the 'students' field using their student_id
            student_data = self.students_collection.find_one(
                {'students.' + student_id: {'$exists': True}}
            )

            if not student_data:
                print(f"No data found for student ID: {student_id}")
                return None

            # Access the student data using the correct student_id
            student_info = student_data['students'].get(student_id, {})
            return student_info

        except Exception as e:
            print(f"Error retrieving student data: {e}")
            return None

    def _classify_intent(self, query: str) -> str:
        """
        Classify user's intent based on keyword matching
        
        Args:
            query (str): User's natural language query
        
        Returns:
            str: Detected intent
        """
        query_lower = query.lower()
        
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return intent
        
        return 'default'

    def preprocess_query(self, query: str, student_id: Optional[str] = None) -> Dict:
        """
        Preprocess and extract intent and entities from user query
        
        Args:
            query (str): User's natural language query
            student_id (str, optional): Student ID extracted from query
        
        Returns:
            Dict containing extracted intent and entities
        """
        # Lowercase the query for consistent matching
        query_lower = query.lower()
        
        # Intent Classification
        detected_intent = self._classify_intent(query)
        
        # Default entities
        entities = {
            'student_id': student_id or 'ST788655',  # Use provided ID or default
            'course_code': None,
            'semester': None
        }
        
        # Additional specific intent classification
        if 'cgpa' in query_lower or 'cumulative gpa' in query_lower:
            detected_intent = 'overall_performance'
        
        # Semester extraction
        try:
            potential_semester = [int(s) for s in query_lower.split() if s.isdigit()]
            entities['semester'] = potential_semester[0] if potential_semester else None
        except Exception:
            entities['semester'] = None
        
        # Course code extraction
        course_codes = ['BUS580', 'BUS628', 'BUS68', 'BUS135', 'BUS972']
        for code in course_codes:
            if code.lower() in query_lower:
                entities['course_code'] = code
                break
        
        return {
            'intent': detected_intent,
            'entities': entities
        }

    def generate_response(self, query_analysis: Dict, student_data: Dict) -> str:
        intent = query_analysis['intent']
    
        if intent == 'overall_performance':
            return self._performance_response(student_data)
        elif intent == 'course_details':
            return self._course_details_response(student_data, query_analysis['entities'])
        elif intent == 'attendance':
            return self._attendance_response(student_data, query_analysis['entities'])
        elif intent == 'semester_performance':
            return self._semester_performance_response(student_data, query_analysis['entities'])
        elif intent == 'current_semester':
            return self._current_semester_response(student_data)
        elif intent == 'credit_status':
            return self._credit_status_response(student_data)
        elif intent == 'program_details':
            return self._program_details_response(student_data)
        elif intent == 'performance_trend':
            return self._performance_trend_response(student_data)
        elif intent == 'attendance_alert':
            return self._attendance_alert_response(student_data)
        elif intent == 'course_load':
            return self._course_load_response(student_data)
        else:
            return "I apologize, but I couldn't understand your specific query. Could you please rephrase?"


    def _performance_response(self, student_data: Dict) -> str:
        """Generate response for overall academic performance"""
        academic_performance = student_data.get('academic_details', {}).get('academic_performance', {})
        
        cgpa = academic_performance.get('cgpa', 'N/A')
        semester_wise_gpa = academic_performance.get('semester_wise_gpa', [])
        current_semester_gpa = semester_wise_gpa[-1]['gpa'] if semester_wise_gpa else 'N/A'
        
        return (f"Your current cumulative GPA is {cgpa}. "
                f"In the current semester, you've achieved a GPA of {current_semester_gpa}. "
                f"Keep up the great work!")

    def _course_details_response(self, student_data: Dict, entities: Dict) -> str:
        """Generate response for course-specific queries"""
        courses = student_data.get('academic_details', {}).get('courses', [])
    
        if entities['course_code']:
        # Find specific course
            specific_course = next(
                (course for course in courses if course['course_code'] == entities['course_code']), 
                None
            )
        
            if specific_course:
                return (f"Course Details for {specific_course['course_code']}: "
                        f"{specific_course['course_name']} "
                        f"taught by {specific_course['instructor']}. "
                        f"Credits: {specific_course['credits']}. "
                        f"This course is in semester {specific_course['semester']}.")
    
    # If no specific course match, provide general course list
        course_list = [f"{c['course_code']}: {c['course_name']}" for c in courses]
        return f"Your current courses are: {', '.join(course_list)}"

    def _attendance_response(self, student_data: Dict, entities: Dict) -> str:
        """Generate response for attendance-related queries"""
        attendance = student_data.get('academic_details', {}).get('attendance', {})
        per_course_attendance = attendance.get('per_course_attendance', [])
    
        if entities['course_code']:
        # Specific course attendance
            course_attendance = next(
                (course for course in per_course_attendance if course['course_code'] == entities['course_code']), 
                None
            )
        
            if course_attendance:
                return (f"Your attendance for {entities['course_code']} is {course_attendance['percentage']}%. "
                        f"You've attended {course_attendance['attended_classes']} out of "
                        f"{course_attendance['total_classes']} classes.")
        
        # Overall attendance
        return (f"Your total attendance is {attendance.get('percentage', 'N/A')}%. "
                f"You've attended {attendance.get('attended_classes', 'N/A')} "
                f"out of {attendance.get('total_classes', 'N/A')} classes.")

    def _semester_performance_response(self, student_data, entities):
       try:
        academic_performance = student_data.get('academic_details', {}).get('academic_performance', {})
        semester_wise_gpa = academic_performance.get('semester_wise_gpa', [])

        # If specific semester is requested
        if entities.get('semester'):
            target_semester = entities['semester']
            semester_data = next(
                (sem for sem in semester_wise_gpa if sem['semester'] == target_semester), 
                None
            )
            
            if semester_data:
                return (
                    f"**Semester {target_semester} Performance**\n"
                    f"• GPA: {semester_data['gpa']}\n"
                    f"• Courses Taken: {semester_data.get('courses_count', 'N/A')}\n"
                    f"• Performance Notes: {semester_data.get('performance_notes', 'No additional notes')}"
                )
        
        # If no specific semester, provide a comprehensive summary
        performance_summary = "\n".join([f"Semester {sem['semester']}: GPA {sem['gpa']}" for sem in semester_wise_gpa])

        # Create a bar chart
        semesters = [sem['semester'] for sem in semester_wise_gpa]
        gpas = [sem['gpa'] for sem in semester_wise_gpa]

        plt.bar(semesters, gpas)
        plt.xlabel('Semester')
        plt.ylabel('GPA')
        plt.title('Semester-wise Performance')
        plt.xticks(rotation=90)

        # Save the plot to a file
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)

        # Convert the image to a base64-encoded string
        img_url = base64.b64encode(img.getvalue()).decode()

        # Return the plot as an image
        return (
            f"**Semester Performance Summary**\n"
            f"{performance_summary}\n"
            f"<img src='data:image/png;base64,{img_url}'>"
        )

       except Exception as e:
        return f"Error retrieving semester performance: {str(e)}"

    def _current_semester_response(self, student_data: Dict) -> str:
        """Generate response for the current semester"""
        enrollment_data = student_data.get('academic_details', {}).get('enrollment', {})
        current_semester = enrollment_data.get('current_semester', 'N/A')
    
        if current_semester != 'N/A':
            return f"Your current semester is {current_semester}."
        else:
            return "Sorry, I couldn't find your current semester information."

    def chat(self, query: str, student_id: Optional[str] = None) -> str:
        """
        Main chat interface method
        
        Args:
            query (str): User's natural language query
            student_id (str, optional): Specific student ID to query
        
        Returns:
            str: Generated response
        """
        # Preprocess query
        query_analysis = self.preprocess_query(query, student_id)
        
        # Use student ID from query analysis
        current_student_id = query_analysis['entities']['student_id']
        
        # Retrieve student data
        student_data = self.retrieve_student_data(current_student_id)
        
        if not student_data:
            return "Sorry, could not find student information. Please check the student ID."
        
        # Generate response
        return self.generate_response(query_analysis, student_data)

    def _calculate_credit_status(self, student_data: Dict) -> Dict:
        """Calculate credit completion status"""
        courses = student_data.get('academic_details', {}).get('courses', [])
        
        current_semester_credits = sum(
            course['credits'] for course in courses 
            if course['semester'] == student_data['academic_details']['enrollment']['current_semester']
        )
        
        return {
            'current_semester_credits': current_semester_credits,
            'credit_distribution': self._get_credit_distribution(courses)
        }

    def _get_credit_distribution(self, courses: List) -> Dict:
        """Get semester-wise credit distribution"""
        distribution = {}
        for course in courses:
            semester = course['semester']
            if semester not in distribution:
                distribution[semester] = 0
            distribution[semester] += course['credits']
        return distribution

    def _analyze_performance_trend(self, student_data: Dict) -> Dict:
        """Analyze semester-wise performance trends"""
        semester_wise_gpa = student_data.get('academic_details', {}).get(
            'academic_performance', {}).get('semester_wise_gpa', []
        )
        
        if not semester_wise_gpa:
            return {'trend': 'No data available'}
            
        gpas = [sem['gpa'] for sem in semester_wise_gpa]
        
        trend = {
            'improving': gpas[-1] > gpas[-2] if len(gpas) > 1 else None,
            'highest_gpa': max(gpas),
            'lowest_gpa': min(gpas),
            'recent_change': gpas[-1] - gpas[-2] if len(gpas) > 1 else 0
        }
        
        return trend

    def _check_attendance_risk(self, student_data: Dict) -> Dict:
        """Check for attendance risks in courses"""
        attendance_data = student_data.get('academic_details', {}).get(
            'attendance', {}).get('per_course_attendance', []
        )
        
        risk_threshold = 75  # Configurable threshold
        at_risk_courses = [
            {
                'course_code': course['course_code'],
                'current_percentage': course['percentage'],
                'classes_needed': self._calculate_classes_needed(
                    course['percentage'], 
                    course['attended_classes'], 
                    course['total_classes'], 
                    risk_threshold
                )
            }
            for course in attendance_data
            if course['percentage'] < risk_threshold
        ]
        
        return {
            'at_risk_courses': at_risk_courses,
            'risk_threshold': risk_threshold
        }

    def _calculate_classes_needed(
        self, current_percentage: float, 
        attended: int, total: int, 
        target: float
    ) -> int:
        """Calculate classes needed to reach target attendance"""
        if current_percentage >= target:
            return 0
            
        current_ratio = attended / total
        classes_needed = 0
        while (attended + classes_needed) / (total + classes_needed) * 100 < target:
            classes_needed += 1
        
        return classes_needed

    def _analyze_course_load(self, student_data: Dict) -> Dict:
        """Analyze current semester course load"""
        courses = student_data.get('academic_details', {}).get('courses', [])
        current_semester = student_data.get('academic_details', {}).get(
            'enrollment', {}).get('current_semester'
        )
        
        current_courses = [
            course for course in courses 
            if course['semester'] == current_semester
        ]
        
        return {
            'total_courses': len(current_courses),
            'total_credits': sum(course['credits'] for course in current_courses),
            'credit_distribution': {
                'one_credit_courses': len([c for c in current_courses if c['credits'] == 1]),
                'four_credit_courses': len([c for c in current_courses if c['credits'] == 4])
            }
        }

    def _program_details_response(self, student_data: Dict) -> str:
        """Generate response for program and enrollment details"""
        enrollment = student_data.get('academic_details', {}).get('enrollment', {})
        
        return (
            f"You are enrolled in the {enrollment.get('program', 'N/A')} program "
            f"in the {enrollment.get('department', 'N/A')} department. "
            f"You were admitted in {enrollment.get('admission_year', 'N/A')}."
        )

    def _credit_status_response(self, student_data: Dict) -> str:
        """Generate response for credit status"""
        credit_status = self._calculate_credit_status(student_data)
        
        return (
            f"You are currently taking {credit_status['current_semester_credits']} "
            f"credits this semester. Your semester-wise credit distribution is: "
            f"{', '.join(f'Semester {sem}: {credits} credits' for sem, credits in credit_status['credit_distribution'].items())}"
        )

    def _performance_trend_response(self, student_data: Dict) -> str:
        """Generate response for performance trend analysis"""
        trend = self._analyze_performance_trend(student_data)
        
        if trend.get('trend') == 'No data available':
            return "Sorry, not enough data to analyze performance trend."
            
        trend_direction = "improving" if trend['improving'] else "declining"
        
        return (
            f"Your academic performance is {trend_direction}. "
            f"Your GPA changed by {abs(trend['recent_change']):.2f} points last semester. "
            f"Your highest GPA so far is {trend['highest_gpa']:.2f}."
        )

    def _attendance_alert_response(self, student_data: Dict) -> str:
        """Generate response for attendance alerts"""
        risk_data = self._check_attendance_risk(student_data)
        
        if not risk_data['at_risk_courses']:
            return "Your attendance is above the minimum requirement in all courses."
            
        risk_messages = [
            f"{course['course_code']}: Currently at {course['current_percentage']}%. "
            f"Need to attend {course['classes_needed']} more classes to reach {risk_data['risk_threshold']}%"
            for course in risk_data['at_risk_courses']
        ]
        
        return (
            f"Attendance Alert: You have {len(risk_data['at_risk_courses'])} courses "
            f"below {risk_data['risk_threshold']}% attendance:\n" + 
            "\n".join(risk_messages)
        )

    def _course_load_response(self, student_data: Dict) -> str:
        """Generate response for course load analysis"""
        load_analysis = self._analyze_course_load(student_data)
        
        return (
            f"You are currently taking {load_analysis['total_courses']} courses "
            f"with a total of {load_analysis['total_credits']} credits. "
            f"This includes {load_analysis['credit_distribution']['one_credit_courses']} "
            f"one-credit courses and "
            f"{load_analysis['credit_distribution']['four_credit_courses']} "
            f"four-credit courses."
        )
        
    def _credit_status_response(self, student_data: Dict) -> str:
        """Comprehensive credit status response"""
        try:
            # Retrieve credit-related information
            academic_details = student_data.get('academic_details', {})
            courses = academic_details.get('courses', [])
            enrollment = academic_details.get('enrollment', {})

            # Calculate total credits
            total_credits_completed = sum(course['credits'] for course in courses)
            current_semester = enrollment.get('current_semester', 'N/A')
            
            # Current semester credits
            current_semester_credits = sum(
                course['credits'] for course in courses 
                if course.get('semester') == current_semester
            )

            # Credit distribution by semester
            credit_distribution = {}
            for course in courses:
                semester = course.get('semester', 'Unknown')
                credit_distribution[semester] = credit_distribution.get(semester, 0) + course['credits']

            # Formatting response
            distribution_str = ", ".join([f"Semester {sem}: {credits} credits" for sem, credits in credit_distribution.items()])

            return (
                f"**Credit Overview**\n"
                f"• Total Credits Completed: {total_credits_completed}\n"
                f"• Current Semester Credits: {current_semester_credits}\n"
                f"• Credit Distribution:\n{distribution_str}"
            )

        except Exception as e:
            return f"Error retrieving credit information: {str(e)}"

    # New function to fetch academic details of two students
    def get_student_details(student_id1, student_id2):
    # Fetch data from database
       student_data1 = retrieve_student_data(student_id1)
       student_data2 = retrieve_student_data(student_id2)
       return student_data1, student_data2

# New function to compare academic details of two students
    def compare_students(student_data1, student_data2):
    # Compare GPA
       gpa1 = student_data1['academic_details']['academic_performance']['cgpa']
       gpa2 = student_data2['academic_details']['academic_performance']['cgpa']
    
    # Compare Credits Completed
       credits1 = student_data1['academic_details']['credits_completed']
       credits2 = student_data2['academic_details']['credits_completed']
    
    # Compare Attendance Percentage
       attendance1 = student_data1['academic_details']['attendance_percentage']
       attendance2 = student_data2['academic_details']['attendance_percentage']
    
    # Prepare comparison data
       comparison_data = {
        'Student 1': {
            'GPA': gpa1,
            'Credits': credits1,
            'Attendance': attendance1
        },
        'Student 2': {
            'GPA': gpa2,
            'Credits': credits2,
            'Attendance': attendance2
        }
       }
    
       return comparison_data

    def _semester_performance_response(self, student_data: Dict, entities: Dict) -> str:
        """Enhanced semester performance response"""
        try:
            academic_performance = student_data.get('academic_details', {}).get('academic_performance', {})
            semester_wise_gpa = academic_performance.get('semester_wise_gpa', [])

            # If specific semester is requested
            if entities.get('semester'):
                target_semester = entities['semester']
                semester_data = next(
                    (sem for sem in semester_wise_gpa if sem['semester'] == target_semester), 
                    None
                )
                
                if semester_data:
                    return (
                        f"**Semester {target_semester} Performance**\n"
                        f"• GPA: {semester_data['gpa']}\n"
                        f"• Courses Taken: {semester_data.get('courses_count', 'N/A')}\n"
                        f"• Performance Notes: {semester_data.get('performance_notes', 'No additional notes')}"
                    )
            
            # If no specific semester, provide a comprehensive summary
            performance_summary = "\n".join([f"Semester {sem['semester']}: GPA {sem['gpa']}" for sem in semester_wise_gpa])

            return (
                f"**Semester Performance Summary**\n"
                f"{performance_summary}\n"
                f"• Cumulative GPA: {academic_performance.get('cgpa', 'N/A')}"
            )

        except Exception as e:
            return f"Error retrieving semester performance: {str(e)}"

    def _performance_trend_response(self, student_data: Dict) -> str:
        """Detailed performance trend analysis"""
        try:
            academic_performance = student_data.get('academic_details', {}).get('academic_performance', {})
            semester_wise_gpa = academic_performance.get('semester_wise_gpa', [])

            if len(semester_wise_gpa) < 2:
                return "Insufficient data to analyze performance trend."

            # Calculate trend
            gpas = [float(sem['gpa']) for sem in semester_wise_gpa]
            trend_change = gpas[-1] - gpas[-2]
            trend_direction = "improving" if trend_change > 0 else "declining"

            return (
                f"**Performance Trend Analysis**\n"
                f"• Overall Trend: {trend_direction}\n"
                f"• GPA Change: {abs(trend_change):.2f} points\n"
                f"• Highest Semester GPA: {max(gpas):.2f}\n"
                f"• Lowest Semester GPA: {min(gpas):.2f}"
            )

        except Exception as e:
            return f"Error analyzing performance trend: {str(e)}"

    
def main():
    chatbot = StudentAcademicChatbot()  # Instantiate the chatbot

    # Interactive chat loop
    while True:
        student_id = input("Enter student ID (or 'exit' to quit): ").strip()
        
        if student_id.lower() in ['exit', 'quit']:
            break
        
        while True:
            user_query = input(f"Ask about student {student_id}'s academic information (or 'back' to change student): ")
            
            if user_query.lower() == 'back':
                break
            
            response = chatbot.chat(user_query, student_id)  # Use the chatbot instance
            print(response)

if __name__ == "__main__":
    main()  # Call the main function to start the chatbot