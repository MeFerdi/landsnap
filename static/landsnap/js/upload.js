document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('.upload-form');
    const fileInputs = form.querySelectorAll('input[type="file"]');
    const submitBtn = form.querySelector('button[type="submit"]');
    
    // File size validation
    fileInputs.forEach(input => {
      input.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
          const maxSize = 10 * 1024 * 1024;
          if (file.size > maxSize) {
            alert('File size exceeds 10MB limit');
            this.value = '';
          }
          
          const previewId = this.id + '-preview';
          const preview = document.getElementById(previewId);
          if (preview) {
            const reader = new FileReader();
            reader.onload = function(e) {
              preview.src = e.target.result;
              preview.style.display = 'block';
            }
            reader.readAsDataURL(file);
          }
        }
      });
    });
    
    form.addEventListener('submit', function(e) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Processing...';
      
      const loadingDiv = document.createElement('div');
      loadingDiv.className = 'loading-indicator';
      loadingDiv.textContent = 'Analyzing images...';
      form.appendChild(loadingDiv);
    });
  });