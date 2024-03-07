import { createApp } from 'vue'
import App from './models/App.vue'
import PrimeVue from 'primevue/config'
import 'primevue/resources/themes/bootstrap4-dark-blue/theme.css';


const app = createApp(App)
app.use(PrimeVue, {ripple:true})
app.mount("#app")
