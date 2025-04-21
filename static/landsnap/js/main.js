    (function() {
      const cssLoaded = document.styleSheets[0].cssRules ? true : false;
      if (!cssLoaded) {
        console.warn('Main CSS failed to load');
        document.body.classList.add('css-failed');
      }
      
      const themeToggle = document.querySelector('.theme-toggle');
      if (themeToggle) {
        themeToggle.addEventListener('click', function() {
          const currentTheme = document.documentElement.getAttribute('data-theme');
          const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
          document.documentElement.setAttribute('data-theme', newTheme);
          localStorage.setItem('theme', newTheme);
        });
      }
      
      document.querySelectorAll('.alert-close').forEach(button => {
        button.addEventListener('click', function() {
          this.closest('.alert').style.display = 'none';
        });
      });
    })();
    window.addEventListener('load', function() {
      if ('connection' in navigator) {
        console.log('Network type:', navigator.connection.effectiveType);
        console.log('Data saver:', navigator.connection.saveData);
      }
      console.log('Page fully loaded');
    })
  const progressCheck = setInterval(function() {
    fetch('/api/analysis-progress/')
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        const progressBar = document.getElementById('progress-bar');
        progressBar.style.width = `${data.progress}%`;
        
        if (data.complete) {
          clearInterval(progressCheck);
          window.location.href = data.redirect_url;
        }
      })
      .catch(error => {
        console.error('Error fetching progress:', error);
      });
  }, 2000);


document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('analysis-form');
  const analyzeBtn = document.getElementById('analyze-btn');
  const spinner = document.getElementById('submit-spinner');
  const btnText = document.getElementById('btn-text');
  

  function setupImagePreview(inputId, previewId, containerId, placeholderId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    const container = document.getElementById(containerId);
    const placeholder = document.getElementById(placeholderId);
    const errorElement = document.getElementById(`error-${inputId}`);
    
    input.addEventListener('change', function(e) {
      const file = e.target.files[0];
      errorElement.textContent = '';
      container.classList.remove('error-border');
      
      if (!file) {
        preview.style.display = 'none';
        preview.removeAttribute('src');
        placeholder.style.display = 'flex';
        return;
      }
      
      const validTypes = ['image/jpeg', 'image/png'];
      const maxSize = 5 * 1024 * 1024;
      let isValid = true;
      
      if (!validTypes.includes(file.type)) {
        errorElement.textContent = 'Please upload a JPEG or PNG image';
        isValid = false;
      }
      
      else if (file.size > maxSize) {
        errorElement.textContent = 'Image must be smaller than 5MB';
        isValid = false;
      }
      
      if (!isValid) {
        input.value = '';
        container.classList.add('error-border');
        return;
      }
      
      const reader = new FileReader();
      reader.onloadstart = function() {
        placeholder.innerHTML = '<span>Loading preview...</span>';
      };
      reader.onload = function(event) {
        preview.src = event.target.result;
        preview.style.display = 'block';
        placeholder.style.display = 'none';
      };
      reader.onerror = function() {
        errorElement.textContent = 'Error loading image preview';
        container.classList.add('error-border');
      };
      reader.readAsDataURL(file);
    });
  }
  
  setupImagePreview('id_image1', 'id_image1-preview', 'preview-container-1', 'placeholder-1');
  setupImagePreview('id_image2', 'id_image2-preview', 'preview-container-2', 'placeholder-2');
  
  form.addEventListener('submit', function(e) {
    let isValid = true;
    const requiredInputs = ['id_image1', 'id_image2'];
    
    requiredInputs.forEach(inputId => {
      const input = document.getElementById(inputId);
      if (!input.files || input.files.length === 0) {
        const errorElement = document.getElementById(`error-${inputId}`);
        errorElement.textContent = 'This field is required';
        isValid = false;
      }
    });
    
    if (!isValid) {
      e.preventDefault();
      analyzeBtn.disabled = false;
      return;
    }
    
    analyzeBtn.disabled = true;
    spinner.style.display = 'inline-block';
    btnText.textContent = 'Processing...';
    
  });
  
  window.addEventListener('pageshow', function(event) {
    if (event.persisted) {
      analyzeBtn.disabled = false;
      spinner.style.display = 'none';
      btnText.textContent = 'Analyze Images';
    }
  });
});