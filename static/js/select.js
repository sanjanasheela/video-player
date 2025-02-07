
  function toggleBackground(checkbox) {
    const listItem = checkbox.closest(".list");
    if (checkbox.checked) {
      listItem.classList.add("checked");
    } else {
      listItem.classList.remove("checked");
    }
  }

function toggleCheckbox(listItem) {
  const checkbox = listItem.querySelector('input[type="checkbox"]');
  checkbox.checked = !checkbox.checked;
  toggleBackground(checkbox);
}


function submitSelected() {
  const form = document.getElementById("fileForm");
  const checkboxes = form.querySelectorAll("input[type='checkbox']");
  
  checkboxes.forEach(checkbox => {
    const timeInput = document.getElementById(`time${checkbox.value}`);
    if (!checkbox.checked) {
      checkbox.disabled = true;
      timeInput.disabled = true;
    }
  });
  
  form.submit();
}

function submitSelected() {
  var originalForm = document.getElementById('fileForm');
  var formData = new FormData();

  originalForm.querySelectorAll('.list').forEach((listItem, index) => {
      var checkbox = listItem.querySelector('input[type="checkbox"]');
      if (checkbox.checked) {
          var fileInput = listItem.querySelector('input[name="files"]');
          var timeInput = listItem.querySelector('input[name="times"]');

          formData.append('files', fileInput.value);
          formData.append('times', timeInput.value || "0"); // Default to 0 if the input is empty
      }
  });

  // Create a new form to submit the filtered data
  var tempForm = document.createElement('form');
  tempForm.method = 'POST';
  tempForm.enctype = 'multipart/form-data';
  tempForm.action = originalForm.action;

  formData.forEach((value, key) => {
      var input = document.createElement('input');
      input.type = 'hidden';
      input.name = key;
      input.value = value;
      tempForm.appendChild(input);
  });

  document.body.appendChild(tempForm);
  tempForm.submit();
}

// for the audio section 