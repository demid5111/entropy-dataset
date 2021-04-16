import neo
import numpy as np

import matplotlib.pyplot as plt

from main.dataset.generation.annotated_edf_signal import AnnotatedEDFSignal


def main():
    # create a reader
    reader = neo.io.Spike2IO(
        filename='/Users/demidovs/Documents/projects/neural-entropy-predictor/data/rats_2018_gdrive/T3/2018.11.13/SN-00000043 - Track 1 - 1164 sec.S2R')
    # read the block
    data = reader.read()[0]
    print(data)
    print('Reading SMR')
    for i, child in enumerate(data.children[0].children):
        print(f'channel {i}: {child.shape}')

    import scipy.io
    mat = scipy.io.loadmat('/Users/demidovs/Documents/projects/neural-entropy-predictor/data/artifacts/ecg_try.mat')
    print('Reading MAT')
    for i, el in enumerate(mat['SN_00000043___Track_1___1164_sec_Ch4'][0][0]):
        if i < 8:
            print(el)
        else:
            print(f'Big array of size: {el.shape}')

    # np.testing.assert_equal(mat['SN_00000043___Track_1___1164_sec_Ch4'][0][0][8], np.reshape(data.children[0].children[3][:, 2], (581500,)))
    from_mat_array = np.array(mat['SN_00000043___Track_1___1164_sec_Ch4'][0][0][8]).flatten()
    from_smr_array = np.array(data.children[0].children[3][:, 3]).flatten()
    np.testing.assert_almost_equal(from_mat_array, from_smr_array, decimal=2)

    print('Reading EDF')
    annotated_edf_signal = AnnotatedEDFSignal.from_edf_file('/Users/demidovs/Documents/projects/neural-entropy-predictor/data/rats_2018_gdrive/T3/2018.11.13/SN-00000043 - Track 1 - 1164 sec.edf')
    print(annotated_edf_signal)

    # importing the modules
    # import numpy as np

    # data to be plotted
    # array = np.array(data.children[0].children[3][:, 3])
    array = np.array(mat['SN_00000043___Track_1___1164_sec_Ch4'][0][0][8])
    x = np.arange(len(array))
    y = array.flatten()

    # plotting
    plt.title("Line graph")
    plt.xlabel("X axis")
    plt.ylabel("Y axis")
    plt.plot(x, y, color="red")
    plt.show()






if __name__ == '__main__':
    main()