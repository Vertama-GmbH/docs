// Open external navigation links in new tab
document.addEventListener('DOMContentLoaded', function() {
  // Find all navigation links
  document.querySelectorAll('.md-nav__link').forEach(function(link) {
    // If it's an external link (has http/https and not our domain)
    if (link.href && (link.href.startsWith('http://') || link.href.startsWith('https://'))) {
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
    }
  });
});
