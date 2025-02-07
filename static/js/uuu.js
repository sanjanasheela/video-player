document.addEventListener("DOMContentLoaded", () => {
    const dropSection = document.querySelector(".drop-section");
    const fileInput = document.querySelector(".file-selector-input");
    const uploadedFilesList = document.querySelector(".list");

    let filesArray = []; // Global array to keep track of all files

    // Trigger file input click when browse button is clicked
    document
      .querySelector(".file-selector")
      .addEventListener("click", () => fileInput.click());

    // Handle file input change event
    fileInput.addEventListener("change", (event) => {
      handleFiles(event.target.files);
    });

    // Handle dragover event to style drop section
    dropSection.addEventListener("dragover", (event) => {
      event.preventDefault();
      dropSection.classList.add("dragover");
    });

    // Handle dragleave event to remove styling
    dropSection.addEventListener("dragleave", () => {
      dropSection.classList.remove("dragover");
    });

    // Handle drop event to process files
    dropSection.addEventListener("drop", (event) => {
      event.preventDefault();
      dropSection.classList.remove("dragover");
      handleFiles(event.dataTransfer.files);
    });

    // Function to process and preview files
    function handleFiles(fileList) {
      for (const file of fileList) {
        if (file.type.startsWith("image/")) {
          if (
            !filesArray.some(
              (f) => f.name === file.name && f.size === file.size
            )
          ) {
            filesArray.push(file); // Add file to global array
            const reader = new FileReader();
            reader.onload = (e) => {
              const img = document.createElement("img");
              img.src = e.target.result;
              uploadedFilesList.appendChild(img);
              var li = document.createElement("li");
              li.classList.add("in-prog");
              li.innerHTML = `
    <div class="col">
        <div class="file-name">
            <div class="name">${file.name}</div>
            <span>0%</span>
        </div>
        <div class="file-progress">
            <span></span>
        </div>
        <div class="file-size">${(file.size / (1024 * 1024)).toFixed(
          2
        )} MB</div>
    </div>
    <hr>
`;
              uploadedFilesList.appendChild(li);
            };
            reader.readAsDataURL(file);
          }
        } else {
          alert("Only image files are allowed.");
        }
      }
      updateFileInput();
    }

    // Function to update file input with all files in the global array
    function updateFileInput() {
      const dataTransfer = new DataTransfer();
      for (const file of filesArray) {
        dataTransfer.items.add(file);
      }
      fileInput.files = dataTransfer.files;
    }
  });