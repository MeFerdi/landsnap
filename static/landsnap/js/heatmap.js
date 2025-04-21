class HeatmapRenderer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.canvas = document.createElement('canvas');
    this.container.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d');
    this.heatmapData = null;
  }
  
  init(imageSrc) {
    const img = new Image();
    img.crossOrigin = 'Anonymous';
    img.onload = () => {
      this.canvas.width = img.width;
      this.canvas.height = img.height;
      this.ctx.drawImage(img, 0, 0);
      this.processImage();
    };
    img.src = imageSrc;
  }
  
  processImage() {
    const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
    this.heatmapData = this.calculateHeatmap(imageData);
    this.renderHeatmap();
  }
  
  calculateHeatmap(imageData) {
    const data = imageData.data;
    const heatmap = [];
    
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];
      const intensity = (r + g + b) / 3;
      heatmap.push(intensity);
    }
    
    return heatmap;
  }
  
  renderHeatmap() {
    // Apply color gradient based on heatmap data
    const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
    
    for (let i = 0; i < this.heatmapData.length; i++) {
      const intensity = this.heatmapData[i];
      const idx = i * 4;
      
      imageData.data[idx] = intensity;
      imageData.data[idx + 1] = 255 - intensity;
      imageData.data[idx + 2] = 0;
    }
    
    this.ctx.putImageData(imageData, 0, 0);
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  const heatmapImg = document.querySelector('.heatmap-img');
  if (heatmapImg) {
    const renderer = new HeatmapRenderer('heatmap-container');
    renderer.init(heatmapImg.src);
  }
});