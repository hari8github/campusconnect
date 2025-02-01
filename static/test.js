document.addEventListener('DOMContentLoaded', () => {
    // DOM Element Selections
    const studentSelector = document.getElementById('student-selector');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const suggestionButtons = document.querySelectorAll('.suggestion-btn');
    const analyticsButtons = document.querySelectorAll('.analytics-btn');
    const compareStudentsBtn = document.getElementById('compare-students-btn');
    const compareStudentsModal = document.getElementById('compare-students-modal');
    const cancelBtn = document.getElementById('cancel-btn');
    const compareBtn = document.getElementById('compare-btn');
    const comparisonTable = document.getElementById('comparison-table');
    const commonDetailsBtn = document.getElementById('common-details-btn');
    const commonDetailsModal = document.getElementById('common-details-modal');
    const commonDetailsTable = document.getElementById('common-details-data');
    const closeCommonDetailsBtn = document.getElementById('close-common-details');
    const sortCriteriaSelect = document.getElementById('sort-criteria');
    const sortOrderBtn = document.getElementById('sort-order-btn');

    // Global Variables for Common Details
    let currentSortCriteria = 'cgpa';
    let isAscending = false;
    let commonDetailsData = []; // Store the original data

    // Initialization Function
    function initializeEventListeners() {
        // Message Sending Events
        sendBtn.addEventListener('click', () => sendMessage());
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        // Student Selector Event
        studentSelector.addEventListener('change', handleStudentSelection);

        // Suggestion and Analytics Buttons
        suggestionButtons.forEach(button => {
            button.addEventListener('click', handleSuggestionClick);
        });

        analyticsButtons.forEach(button => {
            button.addEventListener('click', handleAnalyticsClick);
        });

        // Compare Students Modal Events
        compareStudentsBtn.addEventListener('click', showCompareModal);
        cancelBtn.addEventListener('click', hideCompareModal);
        compareBtn.addEventListener('click', compareStudents);

        // Common Details Modal Events
        commonDetailsBtn.addEventListener('click', fetchCommonDetails);
        closeCommonDetailsBtn.addEventListener('click', () => {
            commonDetailsModal.classList.add('hidden');
        });

        // Sorting Events
        sortCriteriaSelect.addEventListener('change', (e) => {
            currentSortCriteria = e.target.value;
            renderCommonDetailsTable(commonDetailsData);
        });

        sortOrderBtn.addEventListener('click', () => {
            isAscending = !isAscending;
            sortOrderBtn.textContent = isAscending ? '↑ Ascending' : '↓ Descending';
            renderCommonDetailsTable(commonDetailsData);
        });
    }

    // Fetch Common Details
    function fetchCommonDetails() {
        commonDetailsTable.innerHTML = '<tr><td colspan="7" class="text-center">Loading...</td></tr>';
        commonDetailsModal.classList.remove('hidden');

        fetch('/handle_common_details_query', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            commonDetailsData = data; // Store original data
            renderCommonDetailsTable(data);
        })
        .catch(error => {
            console.error('Error:', error);
            commonDetailsTable.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-red-500">
                        Error loading data: ${error.message}
                    </td>
                </tr>
            `;
        });
    }

    // Render table with sorting
    function renderCommonDetailsTable(data) {
        // Sort the data
        const sortedData = [...data].sort((a, b) => {
            const modifier = isAscending ? 1 : -1;
            
            // Handle different sorting criteria
            switch(currentSortCriteria) {
                case 'cgpa':
                    return modifier * (a.cgpa - b.cgpa);
                case 'attendance':
                    return modifier * (a.attendance - b.attendance);
                case 'credits_completed':
                    return modifier * (a.credits_completed - b.credits_completed);
                case 'department':
                    return modifier * a.department.localeCompare(b.department);
                default:
                    return modifier * (a.cgpa - b.cgpa);
            }
        });

        // Clear previous content
        commonDetailsTable.innerHTML = `
            <tr>
                <th class="border border-gray-300 p-2">Rank</th>
                <th class="border border-gray-300 p-2">Name</th>
                <th class="border border-gray-300 p-2">Student ID</th>
                <th class="border border-gray-300 p-2">CGPA</th>
                <th class="border border-gray-300 p-2">Attendance</th>
                <th class="border border-gray-300 p-2">Credits Completed</th>
                <th class="border border-gray-300 p-2">Department</th>
            </tr>
        `;

        // Render sorted data
        sortedData.forEach((student, index) => {
            const row = `
                <tr>
                    <td class="border border-gray-300 p-2">${index + 1}</td>
                    <td class="border border-gray-300 p-2">${student.name}</td>
                    <td class="border border-gray-300 p-2">${student.student_id}</td>
                    <td class="border border-gray-300 p-2">${student.cgpa.toFixed(2)}</td>
                    <td class="border border-gray-300 p-2">${student.attendance.toFixed(1)}%</td>
                    <td class="border border-gray-300 p-2">${student.credits_completed}</td>
                    <td class="border border-gray-300 p-2">${student.department}</td>
                </tr>
            `;
            commonDetailsTable.innerHTML += row;
        });
    }

    // Student Selection Handler
    function handleStudentSelection() {
        const selectedStudent = studentSelector.value;
        if (selectedStudent) {
            resetChatMessages();
            updateWelcomeMessage(selectedStudent);
        }
    }

    // Reset Chat Messages
    function resetChatMessages() {
        while (chatMessages.children.length > 1) {
            chatMessages.removeChild(chatMessages.lastChild);
        }
    }

    // Update Welcome Message
    function updateWelcomeMessage(studentId) {
        const studentName = studentSelector.options[studentSelector.selectedIndex].text.split(' - ')[0];
        const welcomeMessage = `Welcome! You are now viewing academic information for ${studentName}.`;
        chatMessages.firstChild.textContent = welcomeMessage;
    }

    // Suggestion Button Click Handler
    function handleSuggestionClick(event) {
        if (!studentSelector.value) {
            addMessage('bot', 'Please select a student first.');
            return;
        }
        const query = event.target.getAttribute('data-query');
        const fullQuery = getFullQuery(query, studentSelector.value);
        sendMessage(fullQuery);
    }

    // Get Full Query
    function getFullQuery(queryType, studentId) {
        const studentName = studentSelector.options[studentSelector.selectedIndex].text.split(' - ')[0];

        const queries = {
            'courses': `What courses are ${studentName} taking?`,
            'grades': `Show the current grades for ${studentName}`,
            'attendance': `Check attendance for ${studentName}`,
            'gpa': `What is the GPA of ${studentName}?`,
            'credits': `How many credits has ${studentName} completed and how many are needed for graduation?`,
            'enrollment': `Show enrollment details and status for ${studentName}`,
            'schedule': `What is the current class schedule for ${studentName}?`,
            'assignments': `Show pending and upcoming assignments for ${studentName}`,
            'academic_status': `What is the academic standing and status for ${studentName}?`,
            'prerequisites': `What prerequisites are completed and still needed for ${studentName}?`,
            'overall_attendance': 'Show overall attendance ranking',
            'attendance_threshold': 'Show students below attendance threshold',
            'attendance_patterns': 'Show attendance patterns',
            'regular_students': 'Show most regular students',
            'gpa_ranking': 'Show GPA ranking',
            'semester_ranking': 'Show semester-wise ranking',
            'course_ranking': 'Show course-wise ranking'
        };
        return queries[queryType] || queryType;
    }

    // Analytics Button Click Handler
    function handleAnalyticsClick(event) {
        const query = event.target.getAttribute('data-query');
        sendAnalyticsQuery(query);
    }

    // Send Analytics Query
    function sendAnalyticsQuery(query) {
        fetch('/analytics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            addMessage('bot', data.message);
        })
        .catch(error => {
            console.error('Error:', error);
            addMessage('bot', `Error: ${error.message}`);
        });
    }

    // Send Message
    function sendMessage(customMessage = null) {
        if (!studentSelector.value) {
            addMessage('bot', 'Please select a student first.');
            return;
        }

        const message = customMessage || messageInput.value.trim();
        const studentId = studentSelector.value;

        if (!message) return;

        messageInput.value = '';
        addMessage('user', message);
        showTypingIndicator();

        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                student_id: studentId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            removeTypingIndicator();
            addMessage('bot', data.message || 'Sorry, I could not process your request.');
        })
        .catch(error => {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessage('bot', `Error: ${error.message}`);
        });
    }

    // Add Message to Chat
    function addMessage(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`, 'bg-white', 'p-3', 'rounded-lg', 'shadow-sm', 'mb-2');
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Show Typing Indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator flex gap-2 p-3 bg-gray-100 rounded-lg';
        typingDiv.innerHTML = `
            <div class="typing-dot w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
            <div class="typing-dot w-2 h-2 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            <div class="typing-dot w-2 h-2 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
        `;
        typingDiv.id = 'typing-indicator';
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Remove Typing Indicator
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // Show Compare Students Modal
    function showCompareModal() {
        compareStudentsModal.classList.remove('hidden');
    }

    // Hide Compare Students Modal
    function hideCompareModal(event) {
        event.preventDefault();
        compareStudentsModal.classList.add('hidden');
    }

    // Compare Students
    function compareStudents(event) {
        event.preventDefault();
        
        const student1 = document.getElementById('student1').value;
        const student2 = document.getElementById('student2').value;
        
        if (!student1 || !student2) {
            alert('Please select both students for comparison');
            return;
        }

        if (student1 === student2) {
            alert('Please select different students for comparison');
            return;
        }
        
        fetch(`/compare_students?student1=${encodeURIComponent(student1)}&student2=${encodeURIComponent(student2)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                const comparisonData = document.getElementById('comparison-data');
                comparisonData.innerHTML = `
                    <tr>
                        <td class="border border-gray-300 p-2">${data['Student 1'].name}</td>
                        <td class="border border-gray-300 p-2">${data['Student 1'].GPA}</td>
                        <td class="border border-gray-300 p-2">${data['Student 1'].Credits}</td>
                        <td class="border border-gray-300 p-2">${data['Student 1'].Attendance}%</td>
                    </tr>
                    <tr>
                        <td class="border border-gray-300 p-2">${data['Student 2'].name}</td>
                        <td class="border border-gray-300 p-2">${data['Student 2'].GPA}</td>
                        <td class="border border-gray-300 p-2">${data['Student 2'].Credits}</td>
                        <td class="border border-gray-300 p-2">${data['Student 2'].Attendance}%</td>
                    </tr>
                `;
                comparisonTable.classList.remove('hidden');
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to fetch comparison data. Please try again.');
            });
    }

    // Initialize Event Listeners
    initializeEventListeners();
});