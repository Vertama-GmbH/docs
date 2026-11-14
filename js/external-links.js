// Open external navigation links in new tab
document.addEventListener('DOMContentLoaded', function() {
  // Find all navigation links
  document.querySelectorAll('.md-nav__link').forEach(function(link) {
    // Check if it's truly an external link (different hostname)
    if (link.href && link.hostname && link.hostname !== window.location.hostname) {
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
    }
  });
});
