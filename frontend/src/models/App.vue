<template @schedulecalls="addParticipant(s, e, m, a, ev)">
    <v-app>
        <v-app-bar>
        <VTabs v-model="tab">
            <VTab value="viewparticipants">View participant records and schedule phonecalls</VTab>
            <VTab value="addparticipant">Add a new participant</VTab>
        </VTabs>
        </v-app-bar>
        <v-main>
        <VWindow v-model="tab">
            <VWindowItem key="viewparticipants"  value="viewparticipants" :transition="false" :reverse-transition="false">
                <VExpansionPanels>
                    <VExpansionPanel v-if="participants" v-for="p in participants" :title="p.participant_study_id">
                        <VExpansionPanelText>
                            <Participant :participant_study_id="p.participant_study_id" :phone_number="p.phone_number"/>
                        </VExpansionPanelText>
                    </VExpansionPanel>
                </VExpansionPanels>
            </VWindowItem>
            <VWindowItem key="addparticipant" value="addparticipant" :transition="false" :reverse-transition="false">
                <VCard>
                <h1>Add a new participant</h1>
                <v-text-field label="Participant's phone number" 
                    v-model="participant_phone_number"
                    type="tel"
                    hint="Has to have the USA county code +1 in front of it, IE +17631234567"></v-text-field>
                <v-text-field label="Participant study id" v-model="participant_study_id"></v-text-field>
                <ScheduleCalls  @schedulecalls="(s,e,m,a,ev,mm,am,evm) => addParticipant(s,e,m,a,ev,mm,am,evm)">Add Participant</ScheduleCalls>
                </VCard>
            </VWindowItem>
        </VWindow>
        </v-main>
    </v-app>
</template>
<script setup lang="ts">
import {DatePicker} from 'v-calendar'
import Participant from './Participant.vue'
import {DefaultService, type Participant as ParticipantType} from '../client';
import {ref, type Ref} from 'vue'
import ScheduleCalls from './ScheduleCalls.vue'

let tab: Ref<String|null> = ref(null);
let participants: Ref<ParticipantType[]> = ref([])
DefaultService.apiParticipantListApiParticipantListGet().then(
    r => {participants.value = r}
)
function reloadParticipants(){
    DefaultService.apiParticipantListApiParticipantListGet().then(
    r => {participants.value = r}
    )
}
let today = new Date()
today.setHours(0,0,0)
let begin_date = new Date()
let end_date = new Date()
begin_date.setDate(today.getDate()+1)
begin_date.setHours(0,0,0)
end_date.setDate(today.getDate()+14)
end_date.setHours(0,0,0)


const range = ref({
  start: begin_date,
  end: end_date,
});
let participant_study_id = ref("")
let participant_phone_number = ref("")
function addParticipant(s:Date,e:Date,m:number,a:number,ev:number, mm:number, am:number, evm:number){
    DefaultService.addParticipantAddParticipantPost(
        {participant_study_id:participant_study_id.value, 
         phone_number:participant_phone_number.value,
         start_date: s.toISOString(),
         end_date: e.toISOString(),
         morning_time:m,
         afternoon_time:a,
         evening_time:ev,
         morning_minute:mm,
         afternoon_minute:am,
         evening_minute:evm,
                }
    ).then(
        () =>{reloadParticipants()}
    )
}
</script>
