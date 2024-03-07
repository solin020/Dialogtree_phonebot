class ReceiveSpeaker extends AudioWorkletProcessor {
  constructor(options) {
    super()
    this.sampleRate = options.processorOptions.someUsefulVariable
    this.speakerbuflen = Math.floor((0.5*this.sampleRate) / 1024)*1024
    this.speakerbuf = new Float32Array(this.speakerbuflen)
    this.outpointer = 0
    this.inpointer = 0
    this.port.onmessage = (e) => {
        const data = e.data
        const room_at_end = this.speakerbuflen - this.inpointer
        if (data.length>room_at_end){
            this.speakerbuf.set(data.slice(0,room_at_end), this.inpointer)
            this.speakerbuf.set(data.slice(room_at_end))
        }
        else {
            this.speakerbuf.set(data, this.inpointer)
        }
        this.inpointer = (this.inpointer + data.length) % this.speakerbuflen
    }
  }
  process(inputs, outputs, parameters) {
    let opt = outputs[0][0]
    const written_outputs = this.speakerbuf.slice(this.outpointer, this.outpointer + opt.length)
    opt.set(written_outputs)
    this.speakerbuf.set(new Float32Array(opt.length), this.outpointer)
    this.outpointer = (this.outpointer + opt.length) % this.speakerbuflen
    return true;
  }
}

registerProcessor("receive-speaker", ReceiveSpeaker);
