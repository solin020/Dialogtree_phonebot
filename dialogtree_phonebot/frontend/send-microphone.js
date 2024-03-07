class SendMicrophone extends AudioWorkletProcessor {
  constructor(options) {
    super()
    this.sampleRate = options.processorOptions.someUsefulVariable
    this.micbuflen = Math.floor((0.5*this.sampleRate) / 1024)*1024
    this.micbuf = new Float32Array(this.micbuflen)
    this.pointer = 0
  }
  process(inputs, outputs, parameters) {
    this.micbuf.set(inputs[0][0], this.pointer)
    this.pointer = this.pointer + inputs[0][0].length
    if (this.pointer === this.micbuflen){
        this.port.postMessage(this.micbuf)
        this.micbuf = new Float32Array(this.micbuflen)
        this.pointer = 0
    }
    return true;
  }
}

registerProcessor("send-microphone", SendMicrophone);
