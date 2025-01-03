import argparse
import torch
from torchvision import transforms

from dataset import testset
from net import MADFNet
from util.io import load_ckpt
from util.image import unnormalize
from torchvision.utils import save_image
import PIL
import opt
import os

parser = argparse.ArgumentParser()
# training options
parser.add_argument('--list_file', type=str, default='')
parser.add_argument('--snapshot', type=str, default='')
parser.add_argument('--n_refinement_D', type=int, default=2)
parser.add_argument('--image_size', type=int, default=512)
parser.add_argument('--result_dir', type=str, default='results')
args = parser.parse_args()

def evaluate(model, dataset, device, path):
    num = len(dataset)
    
    for i in range(num):
        image, mask, gt, name = zip(*[dataset[i]])
        image = torch.stack(image)
        mask = torch.stack(mask)
        gt = torch.stack(gt)
        with torch.no_grad():
            outputs = model(image.to(device), mask.to(device))
        output = outputs[-1].to(torch.device('cpu'))
        output_comp = mask * image + (1 - mask) * output

        name = name[0]
        name = name.split("/")[-1].replace('.jpg', '.png')
        save_image(unnormalize(output_comp), path + '/' + name)
        save_image(unnormalize(gt), "gt_" + path + '/' + name)

if __name__ == '__main__':
    device = torch.device('cuda')
    if not os.path.exists(args.result_dir):
        os.makedirs(args.result_dir)
    if not os.path.exists('gt_' + args.result_dir):
        os.makedirs('gt_' + args.result_dir)
    
    size = (args.image_size, args.image_size)
    img_transform = transforms.Compose(
        [transforms.Resize(size=size), transforms.ToTensor(),
         transforms.Normalize(mean=opt.MEAN, std=opt.STD)])
    mask_transform = transforms.Compose(
        [transforms.Resize(size=size, interpolation=PIL.Image.NEAREST), transforms.ToTensor()])
    
    dataset_val = testset(args.list_file, img_transform, mask_transform, return_name=True)
    
    model = MADFNet(layer_size=7, args=args).to(device)
    load_ckpt(args.snapshot, [('model', model)])
    
    model.eval()
    evaluate(model, dataset_val, device, args.result_dir)


