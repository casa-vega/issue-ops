document.getElementById('button1').addEventListener('click', function() {
    setActiveButton('button1');
  });
  
  document.getElementById('button2').addEventListener('click', function() {
    setActiveButton('button2');
  });
  
  document.getElementById('button3').addEventListener('click', function() {
    setActiveButton('button3');
  });
  
  function setActiveButton(activeButtonId) {
    var buttons = document.getElementsByClassName('subnav-item');
    for (var i = 0; i < buttons.length; i++) {
      var button = buttons[i];
      if (button.id === activeButtonId) {
        button.setAttribute('aria-current', 'page');
      } else {
        button.removeAttribute('aria-current');
      }
    }
  }
  