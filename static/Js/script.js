document.addEventListener('DOMContentLoaded', () => {
  const menuToggle = document.querySelector('.menu-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', () => {
      navLinks.classList.toggle('active');
    });
  }

  const darkModeButton = document.querySelector('.dark-mode-button');
  if (darkModeButton) {
    darkModeButton.addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
      darkModeButton.classList.toggle('active');
    });
  }
});
