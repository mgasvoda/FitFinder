"""
Image Compression Service for FitFinder
Handles compression of uploaded clothing images to optimize file size and processing speed
"""

import os
import io
import logging
from PIL import Image, ImageOps
from typing import Tuple, Optional, Union
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

class ImageCompressor:
    """
    Handles image compression with configurable quality and size constraints
    """
    
    def __init__(self, 
                 target_size_kb: Tuple[int, int] = (200, 500),
                 max_dimension: int = 1024,
                 jpeg_quality_range: Tuple[int, int] = (75, 85)):
        """
        Initialize the image compressor
        
        Args:
            target_size_kb: Target file size range in KB (min, max)
            max_dimension: Maximum dimension for the longest side in pixels
            jpeg_quality_range: JPEG quality range (min, max)
        """
        self.target_size_kb = target_size_kb
        self.max_dimension = max_dimension
        self.jpeg_quality_range = jpeg_quality_range
        
    def compress_image(self, 
                      input_path: Union[str, Path, io.BytesIO], 
                      output_path: Optional[Union[str, Path]] = None) -> Tuple[str, int]:
        """
        Compress an image to meet size and quality requirements
        
        Args:
            input_path: Path to input image or BytesIO object
            output_path: Path for output image (if None, overwrites input)
            
        Returns:
            Tuple of (output_path, final_size_kb)
        """
        try:
            # Load and validate image
            if isinstance(input_path, io.BytesIO):
                image = Image.open(input_path)
                temp_input = True
            else:
                image = Image.open(input_path)
                temp_input = False
                
            # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            # Auto-rotate based on EXIF data
            image = ImageOps.exif_transpose(image)
            
            # Resize image if needed
            resized_image = self._resize_image(image)
            
            # Determine output path
            if output_path is None:
                if temp_input:
                    # Create temporary file for BytesIO input
                    temp_fd, output_path = tempfile.mkstemp(suffix='.jpg')
                    os.close(temp_fd)
                else:
                    # Overwrite input file
                    output_path = str(input_path).rsplit('.', 1)[0] + '_compressed.jpg'
            
            # Compress with adaptive quality
            final_size_kb = self._compress_with_adaptive_quality(resized_image, output_path)
            
            logger.info(f"Image compressed successfully: {final_size_kb}KB -> {output_path}")
            return str(output_path), final_size_kb
            
        except Exception as e:
            logger.error(f"Error compressing image: {e}")
            raise ValueError(f"Failed to compress image: {str(e)}")
    
    def _resize_image(self, image: Image.Image) -> Image.Image:
        """
        Resize image to fit within max_dimension while maintaining aspect ratio
        
        Args:
            image: PIL Image object
            
        Returns:
            Resized PIL Image object
        """
        width, height = image.size
        
        # Check if resizing is needed
        if max(width, height) <= self.max_dimension:
            return image
            
        # Calculate new dimensions
        if width > height:
            new_width = self.max_dimension
            new_height = int(height * (self.max_dimension / width))
        else:
            new_height = self.max_dimension
            new_width = int(width * (self.max_dimension / height))
            
        # Resize with high-quality resampling
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        logger.info(f"Image resized from {width}x{height} to {new_width}x{new_height}")
        return resized_image
    
    def _compress_with_adaptive_quality(self, image: Image.Image, output_path: str) -> int:
        """
        Compress image with adaptive quality to meet target file size
        
        Args:
            image: PIL Image object
            output_path: Path to save compressed image
            
        Returns:
            Final file size in KB
        """
        min_quality, max_quality = self.jpeg_quality_range
        target_min_kb, target_max_kb = self.target_size_kb
        
        # Start with the maximum quality
        current_quality = max_quality
        
        while current_quality >= min_quality:
            # Save to temporary buffer to check size
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=current_quality, optimize=True)
            size_kb = len(buffer.getvalue()) / 1024
            
            logger.debug(f"Quality {current_quality}: {size_kb:.1f}KB")
            
            # Check if we're within target range
            if target_min_kb <= size_kb <= target_max_kb:
                # Perfect! Save to final location
                with open(output_path, 'wb') as f:
                    f.write(buffer.getvalue())
                return int(size_kb)
            elif size_kb < target_min_kb:
                # File is too small, increase quality slightly and save
                better_quality = min(current_quality + 5, max_quality)
                if better_quality != current_quality:
                    buffer = io.BytesIO()
                    image.save(buffer, format='JPEG', quality=better_quality, optimize=True)
                
                with open(output_path, 'wb') as f:
                    f.write(buffer.getvalue())
                return int(len(buffer.getvalue()) / 1024)
            
            # File is too large, reduce quality
            current_quality -= 5
        
        # If we've exhausted quality options, save with minimum quality
        image.save(output_path, format='JPEG', quality=min_quality, optimize=True)
        final_size = os.path.getsize(output_path) / 1024
        
        logger.warning(f"Could not achieve target size. Final size: {final_size:.1f}KB at quality {min_quality}")
        return int(final_size)
    
    def compress_from_bytes(self, image_bytes: bytes) -> Tuple[bytes, int]:
        """
        Compress image from bytes and return compressed bytes
        
        Args:
            image_bytes: Original image as bytes
            
        Returns:
            Tuple of (compressed_bytes, size_kb)
        """
        input_buffer = io.BytesIO(image_bytes)
        
        # Use temporary file for processing
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Compress to temporary file
            compressed_path, size_kb = self.compress_image(input_buffer, temp_path)
            
            # Read compressed bytes
            with open(compressed_path, 'rb') as f:
                compressed_bytes = f.read()
                
            return compressed_bytes, size_kb
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)


# Singleton instance for the application
default_compressor = ImageCompressor()

def compress_clothing_image(input_path: Union[str, Path, io.BytesIO], 
                          output_path: Optional[Union[str, Path]] = None) -> Tuple[str, int]:
    """
    Convenience function to compress a clothing image using default settings
    
    Args:
        input_path: Path to input image or BytesIO object
        output_path: Optional output path
        
    Returns:
        Tuple of (output_path, final_size_kb)
    """
    return default_compressor.compress_image(input_path, output_path)

def compress_image_bytes(image_bytes: bytes) -> Tuple[bytes, int]:
    """
    Convenience function to compress image bytes using default settings
    
    Args:
        image_bytes: Original image as bytes
        
    Returns:
        Tuple of (compressed_bytes, size_kb)
    """
    return default_compressor.compress_from_bytes(image_bytes) 