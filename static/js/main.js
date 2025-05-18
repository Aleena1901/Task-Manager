// Global state
let token = localStorage.getItem('token');
let tasks = [];

// DOM Elements
const authForms = document.getElementById('authForms');
const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');
const dashboard = document.getElementById('dashboard');
const taskList = document.getElementById('taskList');
const newTaskForm = document.getElementById('newTaskForm');
const navButtons = document.getElementById('navButtons');

// Check token expiration
function isTokenExpired(token) {
    if (!token) return true;
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.exp * 1000 < Date.now();
    } catch (e) {
        return true;
    }
}

// Check authentication status on load
document.addEventListener('DOMContentLoaded', () => {
    if (token && !isTokenExpired(token)) {
        showDashboard();
        loadTasks();
        updateNavigation();
    } else {
        if (token) {
            logout(); // Auto logout if token is expired
        } else {
            showLoginForm();
        }
    }
});

// Show/Hide Forms
function showLoginForm() {
    authForms.classList.remove('hidden');
    loginForm.classList.remove('hidden');
    signupForm.classList.add('hidden');
    dashboard.classList.add('hidden');
    newTaskForm.classList.add('hidden');
}

function showSignupForm() {
    authForms.classList.remove('hidden');
    signupForm.classList.remove('hidden');
    loginForm.classList.add('hidden');
    dashboard.classList.add('hidden');
    newTaskForm.classList.add('hidden');
}

function showDashboard() {
    dashboard.classList.remove('hidden');
    authForms.classList.add('hidden');
    newTaskForm.classList.add('hidden');
}

function showNewTaskForm() {
    newTaskForm.classList.remove('hidden');
    dashboard.classList.add('hidden');
}

function hideNewTaskForm() {
    newTaskForm.classList.add('hidden');
    dashboard.classList.remove('hidden');
}

// Authentication
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch('/api/auth/token', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            token = data.access_token;
            localStorage.setItem('token', token);
            showDashboard();
            loadTasks();
            updateNavigation();
            showToast('Login successful!', 'success');
        } else {
            const error = await response.json();
            showToast(error.detail || 'Invalid email or password', 'error');
        }
    } catch (error) {
        showToast('An error occurred during login', 'error');
        console.error('Login error:', error);
    }
});

signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('signupUsername').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;

    if (!username || !email || !password) {
        showToast('Please fill in all fields', 'error');
        return;
    }

    if (password.length < 8) {
        showToast('Password must be at least 8 characters long', 'error');
        return;
    }

    try {
        const response = await fetch('/api/auth/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ username, email, password }),
        });

        const data = await response.json();

        if (response.ok) {
            token = data.access_token;
            localStorage.setItem('token', token);
            showDashboard();
            loadTasks();
            updateNavigation();
            showToast('Account created successfully!', 'success');
        } else {
            showToast(data.detail || 'Error creating account', 'error');
        }
    } catch (error) {
        showToast('An error occurred during signup', 'error');
        console.error('Signup error:', error);
    }
});

// Task Management
async function loadTasks() {
    if (!token || isTokenExpired(token)) {
        logout();
        return;
    }

    try {
        const response = await fetch('/api/tasks/', {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        if (response.ok) {
            tasks = await response.json();
            renderTasks();
            updateTaskStats();
        } else if (response.status === 401) {
            logout();
        } else {
            showToast('Error loading tasks', 'error');
        }
    } catch (error) {
        showToast('Error loading tasks', 'error');
        console.error('Load tasks error:', error);
    }
}

function renderTasks() {
    taskList.innerHTML = '';
    tasks.forEach(task => {
        const taskElement = createTaskElement(task);
        taskList.appendChild(taskElement);
    });
}

function createTaskElement(task) {
    const div = document.createElement('div');
    div.className = `task-card p-4 bg-white rounded-lg shadow border-l-4 ${getPriorityClass(task.priority)}`;
    div.innerHTML = `
        <div class="flex justify-between items-start">
            <div>
                <h4 class="font-bold text-lg">${task.title}</h4>
                <p class="text-gray-600 mt-1">${task.description}</p>
                <div class="mt-2 text-sm text-gray-500">
                    Due: ${new Date(task.due_date).toLocaleString()}
                </div>
            </div>
            <div class="flex space-x-2">
                <button onclick="editTask(${task.id})" class="text-blue-600 hover:text-blue-800">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                </button>
                <button onclick="deleteTask(${task.id})" class="text-red-600 hover:text-red-800">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                </button>
            </div>
        </div>
    `;
    return div;
}

function getPriorityClass(priority) {
    switch (priority) {
        case 'high':
            return 'priority-high';
        case 'medium':
            return 'priority-medium';
        case 'low':
            return 'priority-low';
        default:
            return '';
    }
}

// Task Form Handling
document.querySelector('#newTaskForm form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = {
        title: document.getElementById('taskTitle').value,
        description: document.getElementById('taskDescription').value,
        priority: document.getElementById('taskPriority').value,
        due_date: document.getElementById('taskDueDate').value,
    };

    try {
        const response = await fetch('/api/tasks/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        });

        if (response.ok) {
            hideNewTaskForm();
            loadTasks();
            showToast('Task created successfully!', 'success');
            e.target.reset();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Error creating task', 'error');
        }
    } catch (error) {
        showToast('An error occurred', 'error');
        console.error('Create task error:', error);
    }
});

// Task Statistics
function updateTaskStats() {
    const ctx = document.getElementById('taskStats').getContext('2d');
    const priorityCounts = {
        high: tasks.filter(t => t.priority === 'high').length,
        medium: tasks.filter(t => t.priority === 'medium').length,
        low: tasks.filter(t => t.priority === 'low').length,
    };

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['High', 'Medium', 'Low'],
            datasets: [{
                data: [priorityCounts.high, priorityCounts.medium, priorityCounts.low],
                backgroundColor: ['#EF4444', '#F59E0B', '#10B981'],
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        }
    });
}

// Toast Notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 p-4 rounded-lg shadow-lg text-white animate__animated animate__fadeIn ${
        type === 'success' ? 'bg-green-600' : 'bg-red-600'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove('animate__fadeIn');
        toast.classList.add('animate__fadeOut');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

// Navigation Update
function updateNavigation() {
    const navButtons = document.getElementById('navButtons');
    if (token && !isTokenExpired(token)) {
        navButtons.innerHTML = `
            <span class="text-gray-600 mr-4">Welcome back!</span>
            <button onclick="logout()" class="bg-white text-indigo-600 border-2 border-indigo-600 px-6 py-2 rounded-lg shadow-sm hover:shadow-md transform hover:-translate-y-0.5 transition-all duration-200">
                Logout
            </button>
        `;
    } else {
        navButtons.innerHTML = `
            <button class="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-2 rounded-lg shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-200" onclick="showLoginForm()">Login</button>
            <button class="bg-white text-indigo-600 border-2 border-indigo-600 px-6 py-2 rounded-lg shadow-sm hover:shadow-md transform hover:-translate-y-0.5 transition-all duration-200" onclick="showSignupForm()">Sign Up</button>
        `;
    }
}

// Logout
function logout() {
    localStorage.removeItem('token');
    token = null;
    tasks = [];
    showLoginForm();
    updateNavigation();
    showToast('Logged out successfully', 'success');
}

// Task Operations
async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;

    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        if (response.ok) {
            loadTasks();
            showToast('Task deleted successfully', 'success');
        } else {
            const error = await response.json();
            showToast(error.detail || 'Error deleting task', 'error');
        }
    } catch (error) {
        showToast('An error occurred', 'error');
        console.error('Delete task error:', error);
    }
}

async function editTask(taskId) {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;

    // Implementation for edit functionality would go here
    // You could create a modal or form to edit the task
    showToast('Edit functionality coming soon!', 'success');
} 