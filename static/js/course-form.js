(function() {
  'use strict';

  function initCourseForm() {
    var schoolLevelSelect = document.getElementById('id_school_level');
    var termSelect = document.getElementById('id_term');
    var subjectSelect = document.getElementById('id_subject');
    var subjectLoading = document.getElementById('subject-loading');
    var createButton = document.getElementById('create-course-btn');

    if (!schoolLevelSelect || !termSelect || !subjectSelect || !createButton) {
      return;
    }

    schoolLevelSelect.classList.add('input-field');
    termSelect.classList.add('input-field');
    subjectSelect.classList.add('input-field');

    function updateButtonState() {
      if (schoolLevelSelect.value && termSelect.value && subjectSelect.value) {
        createButton.disabled = false;
      } else {
        createButton.disabled = true;
      }
    }

    function fetchSubjects() {
      var levelId = schoolLevelSelect.value;
      
      subjectSelect.innerHTML = '<option value="">Select a subject</option>';
      createButton.disabled = true;

      if (!levelId) {
        return;
      }

      if (subjectLoading) {
        subjectLoading.classList.remove('hidden');
        subjectLoading.textContent = 'Loading subjects...';
      }

      fetch('/courses/api/subjects/?school_level=' + levelId)
        .then(function(response) { return response.json(); })
        .then(function(data) {
          data.subjects.forEach(function(subject) {
            var option = new Option(subject.name, subject.id);
            subjectSelect.add(option);
          });
          if (subjectLoading) {
            subjectLoading.classList.add('hidden');
          }
          updateButtonState();
        })
        .catch(function(error) {
          console.error('Error fetching subjects:', error);
          if (subjectLoading) {
            subjectLoading.textContent = 'Failed to load subjects.';
          }
        });
    }

    schoolLevelSelect.addEventListener('change', fetchSubjects);

    termSelect.addEventListener('change', function() {
      subjectSelect.innerHTML = '<option value="">Select a subject</option>';
      createButton.disabled = true;
      fetchSubjects();
    });

    subjectSelect.addEventListener('change', updateButtonState);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCourseForm);
  } else {
    initCourseForm();
  }
})();
