<template>
    <article>
        <h2>Initiate Phonecall</h2>
        <form action="https://chico.ahc.umn.edu/phonebot/stream-conversation" 
                method="post" 
                enctype="application/x-www-form-urlencoded"
                target="phonecall-result">
            <label for="outbound call">Enter the phone number you would like to call.</label>
            <input 
                type="tel" 
                id="outbound call" 
                name="number" 
                pattern="[1]{1}[0-9]{3}[0-9]{3}[0-9]{4}" 
                v-model="called_phone_number"
                required>
            <br>
            <small>Format: 11234567890</small>
            <p>Number being called: {{called_phone_number}}</p>
            <br>
            <input type="submit" value="Call">
            <br>
            <iframe name="phonecall-result"></iframe>
        </form>
    </article>
</template>
<script>
export default {
  data() {
    return {
        called_phone_number: '17632672524',
    }
  }
}
</script>