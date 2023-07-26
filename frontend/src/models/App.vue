<template>
    <main>
        <TabView>
            <TabPanel header="View phonecall logs">
                <CallList/>
            </TabPanel>
            <TabPanel header="Start a phonecall">
                <InitiateCall/>
            </TabPanel>
        </TabView>
    </main>
</template>
<script setup lang="ts">
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import CallList from './CallList.vue'
import InitiateCall from './InitiateCall.vue'
import "primeflex/primeflex.css"; // Import the PrimeVue layout utility library.
</script>