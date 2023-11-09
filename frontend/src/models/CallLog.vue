<template>
  <div v-if="call_log" style="height: 500px; overflow-y: scroll">
    <h1>Call log for {{ $props.date}}</h1>
    <audio controls>
      <source :src="`recordings/bot_${call_sid}.mp3`" type="audio/mpeg">
    </audio>
    <h2>Call answer status: {{ call_log.rejected }}</h2>
    <h2>Free Conversation</h2>
      <h3>Perplexity</h3>
      <div>{{ call_log.perplexity_grade}}</div>
      <h3>Syntax</h3>
      <div>{{ call_log.syntax_grade}}</div>
    <h2>Memory test</h2>
      <h3>Words given</h3>
      <div>{{ call_log.memory_exercise_words}}</div>
      <h3>Initial Test</h3>
      <div>{{ call_log.memory_exercise_reply}}</div>
      <div>{{ call_log.memory_grade}}</div>
      <h3>Recall Test</h3>
      <div>{{ call_log.memory_exercise_reply_2}}</div>
      <div>{{ call_log.memory_grade_2}}</div>
    <h2>Words starting with the letter L Test</h2>
      <h3>Response</h3>
      <div>{{ call_log.l_reply}}</div>
      <h3>Grade</h3>
      <div>{{ call_log.l_grade}}</div>
    <h2>Animal naming test</h2>
      <h3>Response</h3>
      <div>{{ call_log.animal_reply}}</div>
      <h3>Grade</h3>
      <div>{{ call_log.animal_grade}}</div>
    <h2>Full transcript</h2>
    <div>{{ call_log.history}}</div>
  </div>
  <div v-else>Loading</div>
</template>
<script setup lang="ts">
import { ref, type Ref} from 'vue'
import {DefaultService, type CallLog} from '../client';
export interface Props {
    call_sid:string
    date:string
}

let call_log: Ref<CallLog|null> = ref(null);

const props = withDefaults(defineProps<Props>(), {
})
let a = DefaultService.apiCallLogApiCallLogGet(props.call_sid).then(
  (r) => {
    call_log.value = r
  }
)
</script>
 
