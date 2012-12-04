from __future__ import division

import scipy.sparse as sp
import numpy as np

from sklearn.metrics import euclidean_distances
from sklearn.random_projection import (johnson_lindenstrauss_min_dim,
                                       gaussian_random_matrix,
                                       bernouilli_random_matrix,
                                       BernouilliRandomProjection,
                                       GaussianRandomProjection,
                                       )

from sklearn.utils.testing import (assert_less,
                                   assert_raises, assert_raise_message,
                                   assert_array_equal,
                                   assert_equal, assert_almost_equal,
                                   assert_in, assert_not_in
                                   )

from numpy.testing import assert_allclose

sparse_random_projection = [BernouilliRandomProjection]
dense_random_projection = [GaussianRandomProjection]
all_random_projection = set(sparse_random_projection + dense_random_projection)


# Make some random data with uniformly located non zero entries with
# gaussian distributed values
def make_sparse_random_data(n_samples, n_features, n_nonzeros):
    rng = np.random.RandomState(0)
    data_coo = sp.coo_matrix(
        (rng.randn(n_nonzeros),
        (rng.randint(n_samples, size=n_nonzeros),
        rng.randint(n_features, size=n_nonzeros))),
        shape=(n_samples, n_features))
    return data_coo.toarray(), data_coo.tocsr()


n_samples, n_features = (10, 1000)
n_nonzeros = n_samples * n_features / 100.
data, data_csr = make_sparse_random_data(n_samples, n_features, n_nonzeros)


###############################################################################
# test on JL lemma
###############################################################################
def test_invalid_jl_domain():
    assert_raises(ValueError, johnson_lindenstrauss_min_dim, 100, 1.1)
    assert_raises(ValueError, johnson_lindenstrauss_min_dim, 100, 0.0)
    assert_raises(ValueError, johnson_lindenstrauss_min_dim, 100, -0.1)


###############################################################################
# tests on random matrix generation
###############################################################################
def check_input_size_random_matrix(random_matrix):
    assert_raises(ValueError, random_matrix, 0, 0)
    assert_raises(ValueError, random_matrix, -1, 1)
    assert_raises(ValueError, random_matrix, 1, -1)
    assert_raises(ValueError, random_matrix, 1, 0)
    assert_raises(ValueError, random_matrix, -1, 0)


def check_size_generated(random_matrix):
    assert_equal(gaussian_random_matrix(1, 5).shape, (1, 5))
    assert_equal(gaussian_random_matrix(5, 1).shape, (5, 1))
    assert_equal(gaussian_random_matrix(5, 5).shape, (5, 5))
    assert_equal(gaussian_random_matrix(1, 1).shape, (1, 1))


def test_basic_property_of_random_matrix():
    """Check basic properties of random matrix generation"""
    for random_matrix in [gaussian_random_matrix,
                          bernouilli_random_matrix]:

        check_input_size_random_matrix(random_matrix)
        check_size_generated(random_matrix)


def test_gaussian_random_matrix():
    """Check some statical properties of gaussian random matrix"""
    # Check by a monte carlo estimator that each element of the random matrix
    # follow the distribution.
    #
    # Let's say that each element of a_{ij} of A is taken from
    #   a_ij ~ N(0.0, 1 / n_components).
    #
    n_components = 100
    n_features = 1000
    A = gaussian_random_matrix(n_components, n_features, random_state=0)

    assert_allclose(0.0, np.mean(A), atol=0.01)
    assert_allclose(np.var(A, ddof=1), 1 / n_components, rtol=1e-1)


def test_bernouilli_random_matrix():
    """Check some statical properties of (sparse) bernouilli random matrix"""
    # np.unique does not work on .todense sparse matrix
    n_components = 100
    n_features = 500

    for density in [0.3, 1.]:
        s = 1 / density
        A = np.array(bernouilli_random_matrix(n_components,
                                              n_features,
                                              density=density,
                                              random_state=0).todense())

        # Check possible values
        values = np.unique(A)
        assert_in(np.sqrt(s) / np.sqrt(n_components), values)
        assert_in(- np.sqrt(s) / np.sqrt(n_components), values)

        if density == 1.0:
            assert_equal(np.size(values), 2)
        else:
            assert_in(0., values)
            assert_equal(np.size(values), 3)

        # Check by a monte carlo estimator that each element of the
        # random matrix follow the proper distribution.
        #
        # Let's say that each element of a_{ij} of A is taken from
        #
        # - -sqrt(s) / sqrt(n_components)   with probability 1 / 2s
        # -  0                              with probability 1 - 1 / s
        # - +sqrt(s) / sqrt(n_components)   with probability 1 / 2s
        #
        assert_almost_equal(np.mean(A == 0.0),
                            1 - 1 / s, decimal=2)
        assert_almost_equal(np.mean(A == np.sqrt(s) / np.sqrt(n_components)),
                            1 / (2 * s), decimal=2)
        assert_almost_equal(np.mean(A == - np.sqrt(s) / np.sqrt(n_components)),
                            1 / (2 * s), decimal=2)

        assert_almost_equal(np.var(A == 0.0, ddof=1),
                            (1 - 1 / s) * 1 / s, decimal=2)
        assert_almost_equal(np.var(A == np.sqrt(s) / np.sqrt(n_components),
                                   ddof=1),
                            (1 - 1 / (2 * s)) * 1 / (2 * s), decimal=2)
        assert_almost_equal(np.var(A == - np.sqrt(s) / np.sqrt(n_components),
                                   ddof=1),
                            (1 - 1 / (2 * s)) * 1 / (2 * s), decimal=2)


###############################################################################
# tests on random projection transformer
###############################################################################
def test_random_projection_transformer_invalid_input():
    for RandomProjection in all_random_projection:
        assert_raises(ValueError,
                      RandomProjection(n_components='auto').fit, [0, 1, 2])

        assert_raises(ValueError,
                      RandomProjection(n_components=-10).fit, data)

        if RandomProjection in sparse_random_projection:
            assert_raises(
                ValueError,
                BernouilliRandomProjection(density=1.1).fit, data)


def test_try_to_transform_before_fit():
    for RandomProjection in all_random_projection:
        assert_raises(ValueError,
            RandomProjection(n_components='auto').transform, data)


def test_too_many_samples_to_find_a_safe_embedding():
    data, _ = make_sparse_random_data(1000, 100, 1000)

    for RandomProjection in [BernouilliRandomProjection,
                             GaussianRandomProjection]:
        rp = RandomProjection(n_components='auto', eps=0.1)
        expected_msg = (
            'eps=0.100000 and n_samples=1000 lead to a target dimension'
            ' of 5920 which is larger than the original space with'
            ' n_features=100')
        assert_raise_message(ValueError, expected_msg, rp.fit, data)


def test_random_projection_embedding_quality():
    data, _ = make_sparse_random_data(8, 5000, 15000)
    eps = 0.3

    original_distances = euclidean_distances(data, squared=True)
    original_distances = original_distances.ravel()
    non_identical = original_distances != 0.0

    # remove 0 distances to avoid division by 0
    original_distances = original_distances[non_identical]

    for RandomProjection in all_random_projection:
        rp = RandomProjection(n_components='auto', eps=eps, random_state=0)
        projected = rp.fit_transform(data)

        projected_distances = euclidean_distances(projected, squared=True)
        projected_distances = projected_distances.ravel()

        # remove 0 distances to avoid division by 0
        projected_distances = projected_distances[non_identical]

        distances_ratio = projected_distances / original_distances

        # check that the automatically tuned values for the density respect the
        # contract for eps: pairwise distances are preserved according to the
        # Johnson Lindenstrauss bound
        assert_less(distances_ratio.max(), 1 + eps)
        assert_less(1 - eps, distances_ratio.min())


def test_BernouilliRandomProjection_output_representation():
    # when using sparse input, the projected data can be forced to be a
    # dense numpy array
    rp = BernouilliRandomProjection(n_components=10, dense_output=True,
                          random_state=0)
    rp.fit(data)
    assert isinstance(rp.transform(data), np.ndarray)

    sparse_data = sp.csr_matrix(data)
    assert isinstance(rp.transform(sparse_data), np.ndarray)

    # the output can be left to a sparse matrix instead
    rp = BernouilliRandomProjection(n_components=10, dense_output=False,
                                random_state=0)
    rp = rp.fit(data)
    # output for dense input will stay dense:
    assert isinstance(rp.transform(data), np.ndarray)

    # ouput for sparse output will be sparse:
    assert sp.issparse(rp.transform(sparse_data))


def test_random_projection_dimensions():
    for RandomProjection in all_random_projection:
        rp = RandomProjection(n_components='auto', random_state=0).fit(data)

        # the number of components is adjusted from the shape of the training
        # set
        assert_equal(rp.n_components, 'auto')
        assert_equal(rp.n_components_, 110)

        if RandomProjection in sparse_random_projection:
            assert_equal(rp.density, 'auto')
            assert_almost_equal(rp.density_, 0.03, 2)

        assert_equal(rp.components_.shape, (110, n_features))

        projected_1 = rp.transform(data)
        assert_equal(projected_1.shape, (n_samples, 110))

        # once the RP is 'fitted' the projection is always the same
        projected_2 = rp.transform(data)
        assert_array_equal(projected_1, projected_2)

        # fit transform with same random seed will lead to the same results
        rp2 = RandomProjection(random_state=0)
        projected_3 = rp2.fit_transform(data)
        assert_array_equal(projected_1, projected_3)

        # it is also possible to fix the number of components and the density
        # level
        if RandomProjection in sparse_random_projection:
            rp = RandomProjection(n_components=100, density=0.001,
                                  random_state=0)
            projected = rp.fit_transform(data)
            assert_equal(projected.shape, (n_samples, 100))
            assert_equal(rp.components_.shape, (100, n_features))
            assert_less(rp.components_.nnz, 110)  # close to 1% density
            assert_less(90, rp.components_.nnz)  # close to 1% density
