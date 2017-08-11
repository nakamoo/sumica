## 2 models from existing repositories
* Place repository next to HAI
### Faster R-CNN (currently supported)
* Depends on [TensorFlow Object Detection API](https://github.com/tensorflow/models/tree/master/object_detection)
* 80 classes (MS COCO)
* Recommended for GPU

### SSD
* Depends on [this repo](https://github.com/balancap/SSD-Tensorflow)
* 20 classes (PASCAL VOC)
* Recommended for CPU-only computers (fast)

## sending requests
* must include ```image``` as file
* (optional, default:"0.3") ```threshold``` to set confidence threshold [0.0~1.0]
* (optional, default:"false") ```get_image_features``` to get feature map for entire image (3-D array)
* (optional, default:"true") ```get_object_detections``` to get object detections (label, box, confidence)
* (optional, default:"false") ```get_object_features``` to get a feature vector for every object (2-D array)

Warning: Getting object features is slow, getting image features is very slow. Probably need to find a better way to send data and/or use compression.

## format
```
{
  "features": ...,
  "objects": [
    {
      "label": ..,
      "box": ..,
      "confidence": ..,
      "features": ..
    },
    ..
  ]
}
```
