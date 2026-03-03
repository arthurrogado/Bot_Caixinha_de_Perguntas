const webapp = window.Telegram.WebApp;
window.webapp = webapp

function makeUrlParams(params) {
    // this function receives an object and returns a string with the url params
    // if params is already a string, return it
    if(typeof params == 'string') { return params };

    let urlParams = params ? '?' : '' // if params is not null, add '?' to the url
    for (let param in params) {
        urlParams += `${param}=${params[param]}&`
    }
    return urlParams.slice(0, -1) // remove the last '&' from the string
}

function splitOnce(string, separator) {
    let index = string.indexOf(separator)
    return [string.slice(0, index), string.slice(index+1, string.length)]
}

const getParams = () => {
    // This function returns an object with all url params (like id=1&name=2 turns into {id: 1, name: 2})
    let searchString = splitOnce(location.href.toString(), '?')[1]
    let urlSearchParams = new URLSearchParams(searchString)
    let params = {}
    urlSearchParams.forEach((value, key) => {
        params[key] = value
    })
    return params
}

const getStartParams = () => {
    // get params that are important to start the app (like my_drawings, drawings_on, drawings_on_info)
    // and remove the others from the url
    let params = getParams()
    let startParams = {}
    for (let param in params) {
        if(['my_drawings', 'drawings_on', 'drawings_on_info', 'bot_username'].includes(param)) {
            startParams[param] = params[param]
        }
    }
    return startParams
}

// NAVIGATION

const navigateTo = (route, params = null) => {
    // This function changes the url and calls the router function to process the url
    webapp.BackButton.show();
    // join params (object) and getParams() (object too)
    // to maintain the params that are already in the url (like data from bot)
    let objParams = {...params, ...getStartParams()}
    let urlParams = makeUrlParams(objParams)

    history.pushState(null, null, `#${route}${urlParams}`)
    router()
    webapp.MainButton.hide();
}

const router = async () => {
    // This function is executed when the url changes
    // It tests if the url matches with a route and load the route
    // It can also be class and its methods
    const routes = [
        // { path: '/404', component: '404' },
        { path: '/', redirect: '/home' },
        { path: 'home', component: 'home' },
        { path: 'register_drawing', component: 'register_drawing' },
        { path: 'my_drawings', component: 'my_drawings' },
        { path: 'view_drawing', component: 'view_drawing' },
        { path: 'drawings_on', component: 'drawings_on' },
        { path: 'enter_drawing_code', component: 'enter_drawing_code' },
        { path: 'view_drawing_on', component: 'view_drawing_on' }
    ]

    // Test each route for potential match
    const potentialMatches = routes.map(route => {
        return {
            route: route,
            isMatch: location.hash.split('?')[0].replace('#', '') === route.path
        }
    })

    let match = potentialMatches.find(potentialMatch => potentialMatch.isMatch)

    if (!match) {
        navigateTo('home', getParams())
        return
    }

    loadRoute(match.route.component, getParams())
}

const loadRoute = async (route) => {
    // This function loads the html, css and js of the route
    const main = document.querySelector('main');
    main.innerHTML = '';

    try {
        // Load HTML
        const html_response = await fetch(`./pages/${route}/${route}.html`);
        const html_data = await html_response.text();
        main.innerHTML = html_data;

        // Load CSS
        const css_response = await fetch(`./pages/${route}/${route}.css`);
        const css_data = await css_response.text();
        const style = document.createElement('style');
        style.innerHTML = css_data;
        main.appendChild(style);

        // Load JS
        const js_response = await fetch(`./pages/${route}/${route}.js`);
        const js_data = await js_response.text();
        const script = document.createElement('script');
        script.type = 'module';
        script.innerHTML = js_data;
        main.appendChild(script);
        
    } catch (error) {
        console.error(`Erro ao carregar rota ${route}:`, error);
        // Aqui você pode adicionar código para lidar com erros de carregamento
    }
};

const verifyRequiredFields = (formClass = '.form') => {
    // verify if all required fields are filled
    const formElements = document.querySelectorAll(`${formClass} *`)
    let valid = true
    formElements.forEach(element => {
        if(element.required && !element.value) {
            valid = false
        }
    })
    return valid
}

window.verifyRequiredFields = verifyRequiredFields;
window.onpopstate = router;
window.getParams = getParams;
window.navigateTo = navigateTo;

// This function is executed when the DOM is loaded
// so it will be executed only once
document.addEventListener('DOMContentLoaded', () => {
    webapp.BackButton.onClick(() => {
        console.log('## ON CLICK DOM ##')
        webapp.MainButton.hide();
        window.history.back();
    });

    // Add event listener to all elements with 'navigateto' attribute
    // Like a link, button, etc: <button navigateto="home">Home</button> | <a navigateto="home">Home</a>
    document.body.addEventListener('click', (e) => {
        if(e.target.matches('[navigateto]')) {
            e.preventDefault();
            navigateTo(e.target.getAttribute('navigateto'));
        }
    });

    router();
})

export default { navigateTo, getParams, verifyRequiredFields };