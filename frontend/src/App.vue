<template>
  <div class="container">
    <h1>Emotion Detection from Video and Audio</h1>

    <!-- File Upload Section -->
    <div class="upload-section">
      <h3>Upload a Video</h3>
      <FileUpload @file-uploaded="handleFileUpload" />
      <p v-if="message" :class="{'error-message': isError}">{{ message }}</p>
    </div>

    <!-- Uploaded Videos Section -->
    <div v-if="uploadedVideo" class="video-section">
      <h3>Uploaded Video</h3>
      <video :src="uploadedVideo" controls class="small-video"></video>

      <!-- Frame-wise Video and Audio Emotions -->
      <h4>Frame-wise Video and Audio Emotions</h4>
      <div class="frames-container">
        <div v-for="(frame, index) in frames" :key="index" class="frame-item">
          <p>{{ videoEmotions[index].time }}s</p>
          <p>Video Emotion: {{ videoEmotions[index].emotion }}</p>
          <p>Audio Emotion: {{ audioEmotions[index] ? audioEmotions[index].emotion : 'N/A' }}</p>
        </div>
      </div>

      <!-- Emotion Graph -->
      <h4>Combined Emotion Graph</h4>
      <img :src="graph" alt="Emotion Graph" class="emotion-graph" />
      <a :href="graph" target="_blank" download class="btn download-btn">Download Graph</a>
    </div>

    <!-- Loading Overlay -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-popup">
        <img :src="require('@/assets/spinner.gif')" alt="Loading..." />
        <p>Processing... Please wait.</p>
      </div>
    </div>
  </div>
</template>

<script>
import FileUpload from './components/FileUpload.vue';

export default {
  components: {
    FileUpload,
  },
  data() {
    return {
      message: "",
      isError: false,
      uploadedVideo: null,
      frames: [],
      videoEmotions: [],
      audioEmotions: [],
      graph: "",
      loading: false,
    };
  },
  methods: {
    handleFileUpload(file) {
      this.uploadedVideo = URL.createObjectURL(file);
      this.uploadFile(file);
    },
    async uploadFile(file) {
      this.loading = true;
      this.isError = false;
      this.message = "Uploading video...";

      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await fetch("http://127.0.0.1:5000/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Failed to process the video. Please try again.");
        }

        const data = await response.json();
        this.frames = data.frames;
        this.videoEmotions = data.video_emotions;
        this.audioEmotions = data.audio_emotions;
        this.graph = `http://127.0.0.1:5000/${data.graph}`;
        this.message = "Video processing completed!";
      } catch (error) {
        console.error(error);
        this.message = error.message || "Error uploading file. Please try again.";
        this.isError = true;
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.container {
  text-align: center;
  background-color: #ffe6e6; /* Light red background */
  padding: 20px;
}

h1 {
  color: #b33939; /* Dark red for title */
}

.upload-section {
  margin-bottom: 20px;
}

.error-message {
  color: red;
}

input[type="file"] {
  background-color: #b33939; /* Matching upload button color */
  color: white;
  padding: 8px;
  border-radius: 5px;
  border: none;
}

.btn {
  background-color: #b33939; /* Red button */
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  margin-top: 10px;
}

.btn:hover {
  background-color: #ff5e57;
}

.small-video {
  width: 400px; 
  height: auto;
  margin-bottom: 20px;
}

.frames-container {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
}

.frame-item {
  margin: 10px;
  text-align: center;
  width: 120px;
}

.frame-img {
  width: 100px;
  height: auto;
  margin-bottom: 5px;
}

.emotion-graph {
  margin-top: 20px;
  max-width: 100%;
  height: auto;
}

.download-btn {
  display: block;
  margin: 20px auto;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-popup {
  background-color: white;
  padding: 20px;
  border-radius: 10px;
  text-align: center;
}

.loading-popup img {
  width: 50px;
  height: 50px;
}
</style>
