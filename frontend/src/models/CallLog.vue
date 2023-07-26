<template>
  <div v-if="call_log.value">
    <h1>Call by {{call_log.value.number}}</h1>
    <audio controls>
      <source :src="`recordings/bot_${id}.mp3`" type="audio/mpeg">
    </audio>
  </div>
  <div v-else>Loading</div>
</template>
<script setup lang="ts">
import { ref, Ref} from 'vue'
import {DefaultService, CallLog} from '../client';
export interface Props {
    call_log:Ref<CallLog | void>
    timestamp:Ref<string>
    id:string
}
const props = withDefaults(defineProps<Props>(), {
   call_log: () => ref(null),
   timestamp: () => ref(""),
})

DefaultService.apiCallLogApiCallLogCallSidGet(props.id).then(
    r => {
      props.call_log.value = r
      props.timestamp.value = (new Date(r.timestamp)).toString()
    }
)
</script>