<template>
    <h1>Call Logs</h1>
    <Accordion lazy>
        <AccordionTab v-for="c in props.call_list.value" :header="(new Date(c.timestamp)).toString()">
            <CallLog :id="c.call_sid"/>
        </AccordionTab>
    </Accordion>
</template>
<script setup lang="ts">
import {ref, Ref} from 'vue'
import {DefaultService, CallLogHeader} from '../client';
import CallLog from './CallLog.vue'
import Accordion from 'primevue/accordion';
import AccordionTab from 'primevue/accordiontab';
import "primeflex/primeflex.css"; // Import the PrimeVue layout utility library.

export interface Props {
    call_list:Ref<CallLogHeader[]>
}
const props = withDefaults(defineProps<Props>(), {
    call_list: () => ref([])
})

DefaultService.apiCallListApiCallListGet().then(
    r => {props.call_list.value = r}
)
</script>
