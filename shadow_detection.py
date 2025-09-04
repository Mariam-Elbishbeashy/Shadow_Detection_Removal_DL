import os
import cv2
import numpy as np
from tensorflow.keras.applications import VGG16
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Conv2D, Conv2DTranspose, concatenate, BatchNormalization, Input,
    GlobalAveragePooling2D, Dense, Reshape, Multiply
)
from tensorflow.keras.callbacks import ModelCheckpoint
import tensorflow as tf
# from tkinter import Tk, Button, Label, filedialog, messagebox
from PIL import Image 
# from PIL import ImageTk
from shadow_removal import remove_shadow

# ================== CONFIG ==================
IMAGE_SIZE = (384, 512)  # (Height, Width)
DATA_PATH = 'ISTD_Dataset/train'
MODEL_PATH = 'shadow_model2_0850_K2S2E5_aug.h5'
REMOVAL_MODEL_PATH = 'removal_model.h5'
selected_image_path = None
model = None

# =========== data augmentation ==============
def augment_image_and_mask(image, mask):
    augmented = []

    # Original
    augmented.append((image, mask))

    # Horizontal flip
    flipped_img = cv2.flip(image, 1)
    flipped_mask = cv2.flip(mask, 1)
    if len(flipped_mask.shape) == 2:
        flipped_mask = flipped_mask[..., np.newaxis]
    augmented.append((flipped_img, flipped_mask))

    # Brightness adjustment
    brighter = np.clip(image + 0.2, 0, 1)
    augmented.append((brighter, mask))

    # Rotation (15 degrees)
    center = (image.shape[1] // 2, image.shape[0] // 2)
    matrix = cv2.getRotationMatrix2D(center, 15, 1.0)
    rotated_img = cv2.warpAffine(image, matrix, (image.shape[1], image.shape[0]))
    rotated_mask = cv2.warpAffine(mask, matrix, (mask.shape[1], mask.shape[0]))
    if len(rotated_mask.shape) == 2:
        rotated_mask = rotated_mask[..., np.newaxis]
    augmented.append((rotated_img, rotated_mask))

    # Contrast change
    contrast_img = np.clip(image * 1.5, 0, 1)
    augmented.append((contrast_img, mask))

    return augmented

# ============ DATA LOADING FUNCTION ============
def load_images(shadow_folder, mask_folder):
    X, y = [], []
    image_files = sorted(os.listdir(shadow_folder))
    mask_files = sorted(os.listdir(mask_folder))

    for img_file, mask_file in zip(image_files, mask_files):
        img_path = os.path.join(shadow_folder, img_file)
        mask_path = os.path.join(mask_folder, mask_file)

        image = cv2.imread(img_path)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

        if image is not None and mask is not None:
            image = cv2.resize(image, IMAGE_SIZE[::-1]) / 255.0  # (Width, Height)
            mask = cv2.resize(mask, IMAGE_SIZE[::-1]) / 255.0
            mask = np.expand_dims(mask, axis=-1)

            augmented_pairs = augment_image_and_mask(image, mask)
            for aug_img, aug_mask in augmented_pairs:
                X.append(aug_img)
                y.append(aug_mask)

    return np.array(X), np.array(y)

# ============ MODEL COMPONENTS ============
def dilated_conv_block(x, filters, dilation_rate):
    x = Conv2D(filters, 3, padding='same', dilation_rate=dilation_rate, activation='relu')(x)
    x = BatchNormalization()(x)
    return x

def squeeze_excite_block(input_tensor, ratio=16):
    filters = input_tensor.shape[-1]
    se = GlobalAveragePooling2D()(input_tensor)
    se = Dense(filters // ratio, activation='relu')(se)
    se = Dense(filters, activation='sigmoid')(se)
    se = Reshape((1, 1, filters))(se)
    return Multiply()([input_tensor, se])

# ============ MODEL BUILDING FUNCTION ============
def build_model(input_shape=(384, 512, 3)):
    base_model = VGG16(weights='imagenet', include_top=False, input_shape=input_shape)

    for layer in base_model.layers:
        if 'block4' in layer.name or 'block5' in layer.name:
            layer.trainable = True
        else:
            layer.trainable = False

    inputs = base_model.input
    skips = [
        base_model.get_layer("block1_pool").output,
        base_model.get_layer("block2_pool").output,
        base_model.get_layer("block3_pool").output,
        base_model.get_layer("block4_pool").output,
    ]
    x = base_model.output

    x = dilated_conv_block(x, 512, dilation_rate=1)
    x = dilated_conv_block(x, 512, dilation_rate=2)

    for i, skip in zip([256, 128, 64, 32], reversed(skips)):
        x = Conv2DTranspose(i, (2, 2), strides=(2, 2), padding='same')(x)
        x = concatenate([x, skip])
        x = Conv2D(i, 3, activation='relu', padding='same')(x)
        x = BatchNormalization()(x)
        x = squeeze_excite_block(x)

    x = Conv2DTranspose(16, (2, 2), strides=(2, 2), padding='same')(x)
    output = Conv2D(1, 1, activation='sigmoid')(x)
    return Model(inputs=inputs, outputs=output)

# ============ RED OVERLAY FUNCTION ============
def overlay_mask_on_image(original_img_path, predicted_mask):
    original = cv2.imread(original_img_path)
    original = cv2.resize(original, IMAGE_SIZE[::-1])

    if predicted_mask.shape != IMAGE_SIZE:
        predicted_mask = cv2.resize(predicted_mask, IMAGE_SIZE[::-1])

    red_mask = np.zeros_like(original)
    red_mask[:, :, 2] = 255

    binary_mask = (predicted_mask > 120).astype(np.uint8)

    overlay = original.copy()
    overlay[binary_mask == 1] = cv2.addWeighted(original, 0.5, red_mask, 0.5, 0)[binary_mask == 1]

    cv2.imwrite("red_overlay_result.png", overlay)
    print("[INFO] Saved red overlay to red_overlay_result.png")

    return overlay

# ============ GUI CALLBACKS ============
# def choose_image():
#     global selected_image_path, img_label
#     # selected_image_path = filedialog.askopenfilename(filetypes=[("Image Files", ".png;.jpg;*.jpeg")])
#     if selected_image_path:
#         img = Image.open(selected_image_path).resize((640, 480))
#         img_tk = ImageTk.PhotoImage(img)
#         img_label.configure(image=img_tk)
#         img_label.image = img_tk

# ========== Metrics ============
def dice_coefficient(y_true, y_pred):
    y_pred = tf.cast(y_pred > 0.5, tf.float32)
    y_true = tf.cast(y_true, tf.float32)
    intersection = tf.reduce_sum(y_true * y_pred)
    return (2. * intersection + 1) / (tf.reduce_sum(y_true) + tf.reduce_sum(y_pred) + 1)

def iou_score(y_true, y_pred):
    y_pred = tf.cast(y_pred > 0.5, tf.float32)
    y_true = tf.cast(y_true, tf.float32)
    intersection = tf.reduce_sum(y_true * y_pred)
    union = tf.reduce_sum(y_true) + tf.reduce_sum(y_pred) - intersection
    return (intersection + 1) / (union + 1)

# ============ Evaluation ===========
def load_test_data():
    X, y = [], []
    
    shadow_folder = 'ISTD_Dataset/test/test_A'
    mask_folder = 'ISTD_Dataset/test/test_B'
    image_files = sorted(os.listdir(shadow_folder))
    mask_files = sorted(os.listdir(mask_folder))

    for img_file, mask_file in zip(image_files, mask_files):
        img_path = os.path.join(shadow_folder, img_file)
        mask_path = os.path.join(mask_folder, mask_file)

        image = cv2.imread(img_path)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

        if image is not None and mask is not None:
            image = cv2.resize(image, IMAGE_SIZE[::-1]) / 255.0
            mask = cv2.resize(mask, IMAGE_SIZE[::-1]) / 255.0
            mask = np.expand_dims(mask, axis=-1)

            X.append(image)
            y.append(mask)
   
    return np.array(X), np.array(y)

def evaluate_on_test_set():
    X_test, y_test = load_test_data()

    results = model.evaluate(X_test, y_test, batch_size=8)
    print("\n[TEST SET PERFORMANCE]")
    print(f"Loss: {results[0]:.4f}")
    print(f"Dice Coefficient: {results[1]:.4f}")
    print(f"IoU Score: {results[2]:.4f}")
    print(f"Accuracy: {results[3]:.4f}")

# ========== Train and predict ==========
def train_and_predict():
    global model, selected_image_path
    if not selected_image_path:
        print("[ERROR] No image selected.")
        return
    
    if os.path.exists(MODEL_PATH):
        print("[INFO] Loading saved model...")
        model = tf.keras.models.load_model(MODEL_PATH,
                custom_objects={'dice_coefficient': dice_coefficient, 'iou_score': iou_score})
        
        #evaluate_on_test_set()
    else:
        print("[INFO] Loading dataset...")
        shadow_folder = os.path.join(DATA_PATH, 'train_A')
        mask_folder = os.path.join(DATA_PATH, 'train_B')
        X, y = load_images(shadow_folder, mask_folder)
        print("[INFO] Training new model...")

        model = build_model()
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=[dice_coefficient, iou_score, 'accuracy'])
        checkpoint = ModelCheckpoint(MODEL_PATH, monitor='loss', save_best_only=True)
        model.fit(X, y, epochs=5, batch_size=8, callbacks=[checkpoint])

    print("[INFO] Predicting on selected image...")
    predict_and_show(selected_image_path)

#=========== Predict & Show ============
def predict_and_show(image_path):
    image = cv2.imread(image_path)
    resized = cv2.resize(image, IMAGE_SIZE[::-1]) / 255.0
    input_tensor = np.expand_dims(resized, axis=0)

    pred_mask = model.predict(input_tensor)[0].squeeze()
    pred_mask = (pred_mask > 0.5).astype(np.uint8) * 255

    # Remove small noise
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(pred_mask, connectivity=8)
    sizes = stats[1:, -1]  # skip background
    min_size = 500  # tweak as needed
    new_mask = np.zeros_like(pred_mask)

    for i in range(1, num_labels):
        if sizes[i - 1] >= min_size:
            new_mask[labels == i] = 255

    # Optional: Smooth edges
    kernel = np.ones((3, 3), np.uint8)
    new_mask = cv2.morphologyEx(new_mask, cv2.MORPH_CLOSE, kernel)

    pred_mask = new_mask

    edges = cv2.Canny(pred_mask, 100, 200)
    cv2.imwrite("shadow_edges.png", edges)
    print("[INFO] Saved shadow edge map to shadow_edges.png")

    cv2.imwrite("predicted_mask.png", pred_mask)
    print("[INFO] Saved predicted mask to predicted_mask.png")

    overlay_result = overlay_mask_on_image(image_path, pred_mask)

    # mask_img = Image.fromarray(pred_mask).convert("L").resize((640, 480))
    # mask_tk = ImageTk.PhotoImage(mask_img)
    # output_label.configure(image=mask_tk)
    # output_label.image = mask_tk

    # overlay_img = Image.fromarray(cv2.cvtColor(overlay_result, cv2.COLOR_BGR2RGB)).resize((640, 480))
    # overlay_tk = ImageTk.PhotoImage(overlay_img)
    # overlay_label.configure(image=overlay_tk)
    # overlay_label.image = overlay_tk


# def remove_shadows_button():
#     if not selected_image_path:
#         messagebox.showerror("Error", "Please select an image first.")
#         return

#     pred_mask = cv2.imread('predicted_mask.png')
#     if pred_mask is None:
#         messagebox.showerror("Error", "Shadow mask not found.")
#         return

#     result = remove_shadow(selected_image_path, pred_mask)
#     output_path = "shadow_removed_image.jpg"
#     cv2.imwrite(output_path, result)

#     result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
#     img = Image.fromarray(result_rgb)
#     img = ImageTk.PhotoImage(img)

#     removed_shadow_label.config(image=img)
#     removed_shadow_label.image = img

# ============ GUI SETUP ============
# root = Tk()
# root.title("Shadow Detection")

# Button(root, text="Choose Image", command=choose_image, padx=10, pady=5).grid(row=0, column=0, padx=10)
# Button(root, text="Train & Predict", command=train_and_predict, padx=10, pady=5).grid(row=0, column=1, padx=0)
# Button(root, text="Remove Shadows", command=remove_shadows_button, padx=10, pady=5).grid(row=0, column=2, padx=10)

# img_label = Label(root)
# img_label.grid(row=1, column=0, padx=10)

# output_label = Label(root)
# output_label.grid(row=1, column=1, padx=10)

# overlay_label= Label(root)
# overlay_label.grid(row=2, column=0, padx=10)

# removed_shadow_label = Label(root)  
# removed_shadow_label.grid(row=2, column=1, padx=10)

# root.mainloop()
