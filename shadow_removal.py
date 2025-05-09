import cv2
import numpy as np
import matplotlib.pyplot as plt

def compute_histogram_mapping(source, template):

    s_values, bin_idx, s_counts = np.unique(source, return_inverse=True, return_counts=True)
    t_values, t_counts = np.unique(template, return_counts=True)

    # Compute normalized CDFs
    s_quantiles = np.cumsum(s_counts).astype(np.float64)
    s_quantiles /= s_quantiles[-1]

    t_quantiles = np.cumsum(t_counts).astype(np.float64)
    t_quantiles /= t_quantiles[-1]

    interp_t_values = np.interp(s_quantiles, t_quantiles, t_values)
    return interp_t_values[bin_idx]

def remove_shadow(image_path, mask):
    original_img = cv2.imread(image_path)
    corrected_img = original_img.copy()
    height, width, channels = corrected_img.shape

    # Resize mask to match image
    mask = cv2.resize(
        mask, (width, height), interpolation=cv2.INTER_NEAREST
    )

    # Shadow region mask
    shadow_mask = mask[..., 0] != 0

    # Border region for reference (expanded shadow edge)
    kernel = np.ones((25, 25), np.uint8)  # Larger kernel for smoother transition
    dilated_mask = cv2.dilate(mask, kernel, iterations=1)
    border_mask = cv2.subtract(dilated_mask, mask)[..., 0] > 0
    
    plt.imshow(cv2.cvtColor(dilated_mask, cv2.COLOR_BGR2RGB))
    plt.title("Dilated Mask")
    plt.axis('off')
    plt.show()
    border_mask_display = (border_mask.astype(np.uint8)) * 255
    cv2.imshow("Border Mask", border_mask_display)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    # Histogram match each color channel inside shadow to surrounding border
    for c in range(3):  # For R, G, B channels
        channel = original_img[..., c]
        source_pixels = channel[shadow_mask].ravel()
        template_pixels = channel[border_mask].ravel()

        if source_pixels.size == 0 or template_pixels.size == 0:
            continue  # Skip empty masks

        matched = compute_histogram_mapping(source_pixels, template_pixels)

        corrected_channel = corrected_img[..., c]
        corrected_channel[shadow_mask] = np.clip(matched, 0, 255).astype(np.uint8)
        corrected_img[..., c] = corrected_channel

    # Edge blending with Gaussian-blurred mask
    blend_strength = 1.0
    binary_mask = (mask[..., 0] > 0).astype(np.float32)
    alpha = cv2.bilateralFilter(binary_mask, d=9, sigmaColor=75, sigmaSpace=75)
    alpha *= blend_strength
    
    for c in range(3):
        corrected_img[..., c] = (
            alpha * corrected_img[..., c] + (1.0 - alpha) * original_img[..., c]
        ).astype(np.uint8)
        corrected_img[..., c][border_mask] = original_img[..., c][border_mask] 
        
    return corrected_img