<template>
    <h1>Particpant study id : {{props.participant_study_id}}</h1>
    <h2>Particpant phone number : {{props.phone_number}}</h2>
    <dialog ref="deleteParticpantDialog">
        <v-text-field label="Please reenter participant's phone number" 
                    v-model="confirm_phone_number"
                    type="tel"
                    hint="Has to have the USA county code +1 in front of it, IE +17631234567"></v-text-field>
        <v-text-field label="Please reenter participant study id" v-model="confirm_participant_study_id"></v-text-field>
        <v-btn @click="executeDeleteParticpant()">Delete Particpant</v-btn>
        <v-btn @click="closeDeleteParticpant()">Cancel</v-btn>
    </dialog>
    <dialog id="showDayDialog" style="overflow:auto;">
            <h1>Info for {{props.participant_study_id}} on {{show_day_time.toLocaleString()}}</h1>
	    <v-btn @click="closeDay()">Close day viewer</v-btn>
	    <ul>
            <template v-for="a in attributes">
	    <li v-if="sameDay(a.dates, show_day_time)" :key="a.customData.key">
		<div v-if="a.customData.call_type==='future'">
		    <h2>{{new Date(a.customData.time).toLocaleTimeString()}}</h2>
		    <VBtn @click="cancelCall(a.customData)">Cancel Call</VBtn>
		</div>
		<div v-else>
		    <h2>{{new Date(a.customData.timestamp).toLocaleTimeString()}}</h2>
		    <v-btn @click="viewCallLog(a.customData.call_sid)">View Call Log</v-btn>
		    <dialog :id="a.customData.call_sid" style="overflow:auto;">
			<v-btn @click="closeCallLog(a.customData.call_sid)">Close Call Log</v-btn>
			<CallLog  :call_sid="a.customData.call_sid" :date="new Date(a.customData.timestamp).toLocaleString()"></CallLog>
		    </dialog>
		</div>
	    </li>
            </template>
	    </ul>
    </dialog>
    <VTabs v-model="tab">
            <VTab value="overview">View participant call logs</VTab>
            <VTab value="individualcall">Schedule a single call</VTab>
            <VTab value="callschedule">Create a call schedule</VTab>
    </VTabs>
    <VWindow v-model="tab">
        <VWindowItem key="overview"  value="overview" :transition="false" :reverse-transition="false">
            <h1>View participant call logs and future scheduled calls</h1>
            <Calendar :attributes="attributes" >
                <template #day-popover="{day}">
                    <v-btn @click="viewDay(day.date)">View all calls and scheduled calls for this day</v-btn>
                </template>
            </Calendar>
            <h1>Cancel all calls for this participant</h1>
            <v-btn @click="cancelCalls()">Cancel all calls</v-btn>
            <h1>Delete all data for this participant</h1>
            <v-btn @click="openDeleteParticpant()">Delete participant</v-btn>
        </VWindowItem>
        <VWindowItem key="callschedule"  value="callschedule" :transition="false" :reverse-transition="false">
            <ScheduleCalls @schedulecalls="(s,e,m,a,ev,mm,am,evm) => scheduleCalls(s,e,m,a,ev,mm,am,evm)"></ScheduleCalls>
        </VWindowItem>
        <VWindowItem key="individualcall"  value="individualcall" :transition="false" :reverse-transition="false">
            <h1>Schedule an individual call</h1>
            <DatePicker v-model="call_time" mode="dateTime" is24hr ></DatePicker>
            <v-btn @click="scheduleIndividualCall()">Schedule call</v-btn>
        </VWindowItem>
    </VWindow>
</template>
<script setup lang="ts">
import {ref, type Ref, computed} from 'vue'
import {DefaultService, type ScheduledCall, type CallLogHeader} from '../client';
import ScheduleCalls from './ScheduleCalls.vue'
import {DatePicker, Calendar} from 'v-calendar'
import CallLog from './CallLog.vue'
let call_time = ref(new Date())
let show_day_time = ref(new Date())
function sameDay(d1:Date, d2:Date) {
  return (d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate())
}
function viewDay(day:Date){
    show_day_time.value = day;
    (<HTMLDialogElement>document.getElementById("showDayDialog")).showModal()
}
function closeDay(){
    (<HTMLDialogElement>document.getElementById("showDayDialog")).close()
}

export interface Props {
    phone_number:string,
    participant_study_id:string,
}
const props = withDefaults(defineProps<Props>(), {
})
let tab: Ref<String|null> = ref(null);
const scheduled_call_list:Ref<ScheduledCall[]> = ref([]);
const past_call_list:Ref<CallLogHeader[]> = ref([])
let confirm_participant_study_id = ref("")
let confirm_phone_number = ref("")



const deleteParticpantDialog: Ref<HTMLDialogElement|null> = ref(null)
function openDeleteParticpant(){
    if (deleteParticpantDialog.value){
        deleteParticpantDialog.value.showModal()
    }
}
function executeDeleteParticpant(){
    DefaultService.deleteParticipantDeleteParticipantPost(
        confirm_participant_study_id.value, confirm_phone_number.value
    ).then(() => {
        closeDeleteParticpant()
        location.reload()
    })
}
function closeDeleteParticpant(){
    if (deleteParticpantDialog.value){
        deleteParticpantDialog.value.close()
    }
}

function preload(){
    DefaultService.listScheduleCallsListScheduledCallsGet(props.phone_number).then(
        r => {
            scheduled_call_list.value = r
        }
    )
    DefaultService.apiCallListApiCallListGet(props.participant_study_id).then(
        r => {
             past_call_list.value = r
        }
)
}
function cancelCall(c:ScheduledCall){
    let permission = confirm("Are you sure you want to cancel this call?")
    if (permission) {
        DefaultService.cancelCallCancelCallPost(c).then(r=>{preload()})

    }

}
function cancelCalls(){
    let permission = confirm(`Are you sure you want to cancel all calls to ${props.phone_number}?`)
    if (permission) {
        DefaultService.cancelScheduleCallsCancelCallsPost(
        props.phone_number,
     ).then(()=>{preload()})
    }

}

function scheduleIndividualCall(){
    DefaultService.scheduleCallScheduleCallPost({
        id:"",
        phone_number:props.phone_number,
        time:call_time.value.toISOString(),
        rejects:0
    }).then(()=>{preload()})
}

function scheduleCalls(start:Date, end:Date, morning_time:number, afternoon_time:number, evening_time:number, morning_minute:number, afternoon_minute:number,evening_minute:number){
    DefaultService.postScheduleCallsScheduleCallsPost(
        props.phone_number,
        start.toISOString(),
        end.toISOString(),
        morning_time,
        afternoon_time,
        evening_time,
        morning_minute,
        afternoon_minute,
        evening_minute,
    ).then(() => preload())
}
function viewCallLog(call_sid:string){
    (<HTMLDialogElement>document.getElementById(call_sid)).showModal()
}
function closeCallLog(call_sid:string){
    (<HTMLDialogElement>document.getElementById(call_sid)).close()
}

preload()

const attributes = computed<any[]>(() =>{
    const scl: any[] =  scheduled_call_list.value.map(
        c => ({
            key:c.id,
            dot:{
                color:'red'
            },
            dates:new Date(c.time),
            customData:{...c, call_type:'future'},
            popover:true,
        })
    ).reverse()
    const pcl: any[]  = past_call_list.value.map(
        c =>  ({
            key:c.call_sid,
            dot:{
                color:'blue'
            },
            dates:new Date(c.timestamp),
            customData:{...c, id:c.call_sid, call_type:'past'},
            popover:true,
        })
    ).reverse()
    return pcl.concat(scl)
    }
)




</script>
