import app from '../../app.js'

document.querySelectorAll('.option').forEach(option => {
    option.addEventListener('click', (e) => {
        option.id ? app.navigateTo(option.id) : false
    })
})