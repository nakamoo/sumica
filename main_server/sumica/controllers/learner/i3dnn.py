import tensorflow as tf
import numpy as np

import sys
root = "../../../kinetics-i3d"
sys.path.insert(0, root)

import i3d
import cv2

_IMAGE_SIZE = 224
_NUM_CLASSES = 400

_SAMPLE_VIDEO_FRAMES = 10

_CHECKPOINT_PATHS = {
    'rgb': root + '/data/checkpoints/rgb_scratch/model.ckpt',
    'flow': root + '/data/checkpoints/flow_scratch/model.ckpt',
    'rgb_imagenet': root + '/data/checkpoints/rgb_imagenet/model.ckpt',
    'flow_imagenet': root + '/data/checkpoints/flow_imagenet/model.ckpt',
}

_LABEL_MAP_PATH = root + '/data/label_map.txt'

class I3DNN:
    def __init__(self, device_list="1"):
          eval_type = 'rgb'
          imagenet_pretrained = True

          if eval_type not in ['rgb', 'flow', 'joint']:
            raise ValueError('Bad `eval_type`, must be one of rgb, flow, joint')

          self.kinetics_classes = [x.strip() for x in open(_LABEL_MAP_PATH)]

          if eval_type in ['rgb', 'joint']:
            # RGB input has 3 channels.
            rgb_input = tf.placeholder(
                tf.float32,
                shape=(1, _SAMPLE_VIDEO_FRAMES, _IMAGE_SIZE, _IMAGE_SIZE, 3))
            with tf.variable_scope('RGB'):
              rgb_model = i3d.InceptionI3d(
                  _NUM_CLASSES, spatial_squeeze=True, final_endpoint='Logits')
              rgb_logits, ends = rgb_model(
                  rgb_input, is_training=False, dropout_keep_prob=1.0)
            self.feats = ends['Mixed_5c']
            rgb_variable_map = {}
            for variable in tf.global_variables():
              if variable.name.split('/')[0] == 'RGB':
                rgb_variable_map[variable.name.replace(':0', '')] = variable
            rgb_saver = tf.train.Saver(var_list=rgb_variable_map, reshape=True)

          if eval_type in ['flow', 'joint']:
            # Flow input has only 2 channels.
            flow_input = tf.placeholder(
                tf.float32,
                shape=(1, _SAMPLE_VIDEO_FRAMES, _IMAGE_SIZE, _IMAGE_SIZE, 2))
            with tf.variable_scope('Flow'):
              flow_model = i3d.InceptionI3d(
                  _NUM_CLASSES, spatial_squeeze=True, final_endpoint='Logits')
              flow_logits, _ = flow_model(
                  flow_input, is_training=False, dropout_keep_prob=1.0)
            flow_variable_map = {}
            for variable in tf.global_variables():
              if variable.name.split('/')[0] == 'Flow':
                flow_variable_map[variable.name.replace(':0', '')] = variable
            flow_saver = tf.train.Saver(var_list=flow_variable_map, reshape=True)

          if eval_type == 'rgb':
            self.model_logits = rgb_logits
          elif eval_type == 'flow':
            model_logits = flow_logits
          else:
            model_logits = rgb_logits + flow_logits
          self.model_predictions = tf.nn.softmax(self.model_logits)
          self.rgb_input = rgb_input

          config = tf.ConfigProto(gpu_options=tf.GPUOptions(visible_device_list=device_list))
          sess = tf.Session(config=config)
          self.sess = sess
          if eval_type in ['rgb', 'joint']:
              if imagenet_pretrained:
                rgb_saver.restore(sess, _CHECKPOINT_PATHS['rgb_imagenet'])
              else:
                rgb_saver.restore(sess, _CHECKPOINT_PATHS['rgb'])

          if eval_type in ['flow', 'joint']:
              if imagenet_pretrained:
                flow_saver.restore(sess, _CHECKPOINT_PATHS['flow_imagenet'])
              else:
                flow_saver.restore(sess, _CHECKPOINT_PATHS['flow'])
                
    def process_image(self, img):
        # (1, _SAMPLE_VIDEO_FRAMES, 224, 224, 3)
        feed_dict = {}
        feed_dict[self.rgb_input] = img

        out_logits, out_predictions, out_feats = self.sess.run(
            [self.model_logits, self.model_predictions, self.feats],
            feed_dict=feed_dict)

        feats = np.max(out_feats, axis=(0, 1, 2, 3))
        out_logits = out_logits[0]
        out_predictions = out_predictions[0]
        sorted_indices = np.argsort(out_predictions)[::-1]

        #print('Norm of logits: %f' % np.linalg.norm(out_logits))
        #print('\nTop classes and probabilities')
        for index in sorted_indices[:1]:
            print(out_predictions[index], out_logits[index], self.kinetics_classes[index])

            return out_predictions[index], out_logits[index], self.kinetics_classes[index], feats.tolist()

if __name__ == '__main__':
  nn = I3DNN()
  img = cv2.imread("pasta.jpg")[:,:,[2,1,0]]/128.0-1.0
  img = cv2.resize(img, (224, 224))
  img = np.array([[img for _ in range(_SAMPLE_VIDEO_FRAMES)]])
  print(img.shape)
  probs, logits, label = nn.process_image(img)
  print(probs, logits, label)
