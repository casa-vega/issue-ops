// document.getElementById('button1').addEventListener('click', function() {
//     setActiveButton('button1');
// });

// document.getElementById('button2').addEventListener('click', function() {
//   setActiveButton('button2');
// });

// document.getElementById('button3').addEventListener('click', function() {
//   setActiveButton('button3');
// });

// function setActiveButton(activeButtonId) {
//   var buttons = document.getElementsByClassName('subnav-item');
//   for (var i = 0; i < buttons.length; i++) {
//     var button = buttons[i];
//     if (button.id === activeButtonId) {
//       button.setAttribute('aria-current', 'page');
//     } else {
//       button.removeAttribute('aria-current');
//     }
//   }
// }


function openTab(evt, tabName) {
  // Declare all variables
  var i, tabcontent, tablinks;

  // Get all elements with class="tabcontent" and hide them
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  // Get all elements with class="tabnav-tab" and remove the class "active" and "aria-current"
  tablinks = document.getElementsByClassName("tabnav-tab");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].classList.remove("active");
    tablinks[i].setAttribute("aria-current", "false");
  }

  // Show the current tab
  document.getElementById(tabName).style.display = "block";

  // Add an "active" class to the link that opened the tab
  var activeTab;
  if (evt) {
    activeTab = evt.currentTarget;
  } else {
    activeTab = document.querySelector(`.tabnav-tab[onclick="openTab(event, '${tabName}')"]`);
  }
  activeTab.classList.add("active");
  activeTab.setAttribute("aria-current", "page");
}

window.onload = function() {
  openTab(null, 'Organization');
}

