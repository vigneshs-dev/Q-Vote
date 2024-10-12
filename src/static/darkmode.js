
function addDarkmodeWidget() {
const options = {
    bottom: '64px', // default: '32px'
    right: '32px', // default: '32px'
    left: 'unset', // default: 'unset'
    time: '0.5s', // default: '0.3s'
    mixColor: '#e5e5e5', // default: '#fff'    
    backgroundColor: '#fff',  // default: '#fff'
    buttonColorDark: '#fff',  // default: '#100f2c'
    buttonColorLight: '#3C3D37', // default: '#fff'
    saveInCookies: true, // default: true,
    label: '🌖', // default: ''
    autoMatchOsTheme: true // default: true
  }
  
const darkmode = new Darkmode(options);
darkmode.showWidget();
}
window.addEventListener('load', addDarkmodeWidget);
