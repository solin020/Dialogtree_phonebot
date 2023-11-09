<template>
    <h1>Create call schedule</h1>
    <DatePicker  mode="date" v-model.range="range" :columns="2">
        <template #footer>
            <v-sheet style="width:35vw;">
            <p>Please note that SALSA can only handle one call at a time and if multiple participants
               are scheduled to recieve a call at the same time SALSA will call them one by one,
               with each call lasting for a bit less than 10 minutes.
            </p>
            </v-sheet>
        </template>
    </DatePicker>
    <v-text-field label="Choose when the participant would like to recieve their morning call" type="time" v-model="morning_time" min="00:00" max="12:00" />
    <v-text-field label="Choose when the participant would like to recieve their midday call" type="time" v-model="afternoon_time" min="06:00" max="18:00" />
    <v-text-field label="Choose when the participant would like to recieve their evening call" type="time" v-model="evening_time" min="12:00" max="23:59" />    <v-btn @click="callScheduleEmit()"><slot>Create call schedule</slot></v-btn>
</template>
<script setup lang="ts">
import {DatePicker, Calendar} from 'v-calendar'
import {ref, type Ref, computed} from 'vue'

const emit = defineEmits<{
  (e: 'schedulecalls', start_date: Date, end_date: Date, morning_time:number, afternoon_time:number, evening_time:number, morning_minute:number, afternoon_minute:number, evening_minute:number): void
}>()
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

let morning_time = ref("08:00")
let afternoon_time = ref("13:00")
let evening_time = ref("18:00")
function callScheduleEmit(){
    emit('schedulecalls',
    range.value.start,
    range.value.end,
    parseInt(morning_time.value.split(":")[0]),
    parseInt(afternoon_time.value.split(":")[0]),
    parseInt(evening_time.value.split(":")[0]),
    parseInt(morning_time.value.split(":")[1]),
    parseInt(afternoon_time.value.split(":")[1]),
    parseInt(evening_time.value.split(":")[1])
    )
}

</script>
