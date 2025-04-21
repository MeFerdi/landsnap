class HeatmapRenderer {
  constructor(containerId, beforeImgUrl, afterImgUrl, heatmapUrl) {
    this.container = document.getElementById(containerId);
    this.beforeImgUrl = beforeImgUrl;
    this.afterImgUrl = afterImgUrl;
    this.heatmapUrl = heatmapUrl;
    this.init();
  }
  
  init() {
    this.canvas = document.createElement('canvas');
    this.container.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d');
    
 
    this.canvas.width = this.container.clientWidth;
    this.canvas.height = this.container.clientHeight;
    
    
    this.loadHeatmap();
  }
  
  loadHeatmap() {
    const img = new Image();
    img.crossOrigin = 'Anonymous';
    img.onload = () => {
    
      const ratio = Math.min(
        this.canvas.width / img.width,
        this.canvas.height / img.height
      );
      const width = img.width * ratio;
      const height = img.height * ratio;
      
    
      const x = (this.canvas.width - width) / 2;
      const y = (this.canvas.height - height) / 2;
      
      this.ctx.drawImage(img, x, y, width, height);
      
    
      this.applyHeatmapEffect();
    };
    img.src = this.heatmapUrl;
  }
  
  applyHeatmapEffect() {
    const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
    const data = imageData.data;
    
    for (let i = 0; i < data.length; i += 4) {
      const intensity = data[i];
      
      // Apply heatmap color gradient
      data[i] = intensity;
      data[i + 1] = Math.max(0, 255 - intensity * 1.5);
      data[i + 2] = 0;
    }
    
    this.ctx.putImageData(imageData, 0, 0);
  }
}

// Initialize heatmaps for all results
document.addEventListener('DOMContentLoaded', function() {
  const heatmapPreviews = document.querySelectorAll('.heatmap-preview');
  
  heatmapPreviews.forEach((preview, index) => {
    const containerId = `heatmap-container-${index + 1}`;
    const beforeImg = preview.dataset.beforeImg;
    const afterImg = preview.dataset.afterImg;
    const heatmapImg = preview.dataset.heatmapImg;
    
    new HeatmapRenderer(
      containerId,
      beforeImg,
      afterImg,
      heatmapImg
    );
  });
});