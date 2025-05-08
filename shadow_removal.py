import cv2
import numpy as np

def remove_shadow(image_path, thresholded_mask_resized):
    original_img = cv2.imread(image_path)

    corrected_img = original_img.copy()
    # Get the dimensions of corrected_img
    height, width, channels = corrected_img.shape

    # Print the dimensions
    print(f"Height: {height}, Width: {width}, Channels: {channels}")
    thresholded_mask_resized = cv2.resize(
        thresholded_mask_resized, (original_img.shape[1], original_img.shape[0]), interpolation=cv2.INTER_NEAREST
    )

    shadow_pixels_r = original_img[thresholded_mask_resized[..., 0] == 0, 0]
    shadow_pixels_g = original_img[thresholded_mask_resized[..., 0] == 0, 1]
    shadow_pixels_b = original_img[thresholded_mask_resized[..., 0] == 0, 2]

    mean_shadow_intensity_r = np.mean(shadow_pixels_r) / 255.0 if len(shadow_pixels_r) > 0 else 0.5
    mean_shadow_intensity_g = np.mean(shadow_pixels_g) / 255.0 if len(shadow_pixels_g) > 0 else 0.5
    mean_shadow_intensity_b = np.mean(shadow_pixels_b) / 255.0 if len(shadow_pixels_b) > 0 else 0.5

    # Dynamic gamma adjustment based on shadow brightness for each channel
    gamma_r = 0.2 + (1.0 - mean_shadow_intensity_r) * 0.8
    gamma_g = 0.1 + (1.0 - mean_shadow_intensity_g) * 0.9
    gamma_b = 0.1 + (1.0 - mean_shadow_intensity_b) * 0.9

    print(f"Gamma R: {gamma_r}, Gamma G: {gamma_g}, Gamma B: {gamma_b}")

    # Apply gamma correction separately for each channel
    for i in range(width):
        for j in range(height):
            if thresholded_mask_resized[j, i, 0] == 0: 
                corrected_img[j, i, 0] = 255
                corrected_img[j, i, 1] = 255
                corrected_img[j, i, 2] = 255
            else:
                corrected_img[j, i, 0] = np.power((corrected_img[j, i, 0] / 255), gamma_r) * 255
                corrected_img[j, i, 1] = np.power((corrected_img[j, i, 1] / 255), gamma_g) * 255
                corrected_img[j, i, 2] = np.power((corrected_img[j, i, 2] / 255), gamma_b) * 255

    # Restore background pixels as they are
    for i in range(width):
        for j in range(height):
            if thresholded_mask_resized[j, i, 0] == 0: 
                corrected_img[j, i, 0] = original_img[j, i, 0]
                corrected_img[j, i, 1] = original_img[j, i, 1]
                corrected_img[j, i, 2] = original_img[j, i, 2]

     # Smooth edges using a Gaussian blur
    mask = thresholded_mask_resized[..., 0]
    blurred_mask = cv2.GaussianBlur(mask.astype(np.float32), (15, 15), 5)

    for c in range(channels):
        corrected_img[..., c] = (corrected_img[..., c] * blurred_mask / 255.0 +
                                 original_img[..., c] * (1 - blurred_mask / 255.0)).astype(np.uint8)
        
    return corrected_img