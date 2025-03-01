document.addEventListener('DOMContentLoaded', function() {
    // Add any JavaScript functionality if needed

    function updateUI(eventType, data) {
        if (eventType === 'class_updated') {
            // Update the UI for class changes
            const classElements = document.querySelectorAll(`[data-class-name="${data.old_class_name}"]`);
            classElements.forEach(el => el.textContent = data.new_class_name);
        } else if (eventType === 'subject_updated') {
            // Update the UI for subject changes
            const subjectElements = document.querySelectorAll(`[data-subject-code="${data.subject_code}"]`);
            subjectElements.forEach(el => el.textContent = data.new_subject_name);
        } else if (eventType === 'user_updated') {
            // Update the UI for user changes
            const userElements = document.querySelectorAll(`[data-user-id="${data.user_id}"]`);
            userElements.forEach(el => el.textContent = data.new_username);
        } else if (eventType === 'teacher_updated') {
            // Update the UI for teacher changes
            const teacherElements = document.querySelectorAll(`[data-teacher-id="${data.teacher_id}"]`);
            teacherElements.forEach(el => el.textContent = data.new_teacher_name);
        }
        // Handle more event types as needed
    }

    // Example of listening to an event
    document.addEventListener('class_updated', function(e) {
        updateUI('class_updated', e.detail);
    });

    document.addEventListener('subject_updated', function(e) {
        updateUI('subject_updated', e.detail);
    });

    document.addEventListener('user_updated', function(e) {
        updateUI('user_updated', e.detail);
    });

    document.addEventListener('teacher_updated', function(e) {
        updateUI('teacher_updated', e.detail);
    });
});