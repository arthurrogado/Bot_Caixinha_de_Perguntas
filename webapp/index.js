import app from './app.js'

document.querySelector('#home button').addEventListener('click', () => {
    app.navigateTo('home')
})