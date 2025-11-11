# Library Features
## abort_unwind

The tracking issue for this feature is: #130338

## acceptfilter

The tracking issue for this feature is: #121891

## addr_parse_ascii

The tracking issue for this feature is: #101035

## align_to_uninit_mut

The tracking issue for this feature is: #139062

## alloc_error_hook

The tracking issue for this feature is: #51245

## alloc_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## alloc_layout_extra

The tracking issue for this feature is: #55724

## alloc_slice_into_array

The tracking issue for this feature is: #148082

## allocator_api

The tracking issue for this feature is #32838

Sometimes you want the memory for one collection to use a different allocator than the memory for another collection. In this case, replacing the global allocator is not a workable option. Instead, you need to pass in an instance of an AllocRef to each collection for which you want a custom allocator.

TBD

## alloctests

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## arc_is_unique

The tracking issue for this feature is: #138938

## array_into_iter_constructors

The tracking issue for this feature is: #91583

## array_ptr_get

The tracking issue for this feature is: #119834

## array_try_from_fn

The tracking issue for this feature is: #89379

## array_try_map

The tracking issue for this feature is: #79711

## array_windows

The tracking issue for this feature is: #75027

## ascii_char

The tracking issue for this feature is: #110998

## ascii_char_variants

The tracking issue for this feature is: #110998

## assert_matches

The tracking issue for this feature is: #82775

## async_fn_traits

See Also: fn_traits

The async_fn_traits feature allows for implementation of the AsyncFn* traits for creating custom closure-like types that return futures.

The main difference to the Fn* family of traits is that AsyncFn can return a future that borrows from itself (FnOnce::Output has no lifetime parameters, while AsyncFnMut::CallRefFuture does).

## async_gen_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## async_iter_from_iter

The tracking issue for this feature is: #81798

## async_iterator

The tracking issue for this feature is: #79024

## atomic_from_mut

The tracking issue for this feature is: #76314

## atomic_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## atomic_try_update

The tracking issue for this feature is: #135894

## autodiff

The tracking issue for this feature is: #124509

## backtrace_frames

The tracking issue for this feature is: #79676

## bigint_helper_methods

The tracking issue for this feature is: #85532

## bikeshed_guaranteed_no_drop

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## binary_heap_drain_sorted

The tracking issue for this feature is: #59278

## binary_heap_into_iter_sorted

The tracking issue for this feature is: #59278

## binary_heap_peek_mut_refresh

The tracking issue for this feature is: #138355

## bool_to_result

The tracking issue for this feature is: #142748

## bound_as_ref

The tracking issue for this feature is: #80996

## bound_copied

The tracking issue for this feature is: #145966

## box_as_ptr

The tracking issue for this feature is: #129090

## box_into_boxed_slice

The tracking issue for this feature is: #71582

## box_into_inner

The tracking issue for this feature is: #80437

## box_take

The tracking issue for this feature is: #147212

## box_vec_non_null

The tracking issue for this feature is: #130364

## breakpoint

The tracking issue for this feature is: #133724

## bstr

The tracking issue for this feature is: #134915

## bstr_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## btree_cursors

The tracking issue for this feature is: #107540

## btree_set_entry

The tracking issue for this feature is: #133549

## btreemap_alloc

The tracking issue for this feature is: #32838

## buf_read_has_data_left

The tracking issue for this feature is: #86423

## bufreader_peek

The tracking issue for this feature is: #128405

## c_size_t

The tracking issue for this feature is: #88345

## c_void_variant

This feature is internal to the Rust compiler and is not intended for general use.

## can_vector

The tracking issue for this feature is: #69941

## cast_maybe_uninit

The tracking issue for this feature is: #145036

## cell_get_cloned

The tracking issue for this feature is: #145329

## cell_leak

The tracking issue for this feature is: #69099

## cfg_accessible

The tracking issue for this feature is: #64797

## cfg_eval

The tracking issue for this feature is: #82679

## cfg_select

The tracking issue for this feature is: #115585

## char_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## char_max_len

The tracking issue for this feature is: #121714

## clone_to_uninit

The tracking issue for this feature is: #126799

## cmp_minmax

The tracking issue for this feature is: #115939

## coerce_pointee_validated

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## coerce_unsized

The tracking issue for this feature is: #18598

## cold_path

The tracking issue for this feature is: #136873

## concat_bytes

The tracking issue for this feature is: #87555

## const_alloc_error

The tracking issue for this feature is: #92523

## const_btree_len

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## const_carrying_mul_add

The tracking issue for this feature is: #85532

## const_cell_traits

The tracking issue for this feature is: #147787

## const_clone

The tracking issue for this feature is: #142757

## const_cmp

The tracking issue for this feature is: #143800

## const_control_flow

The tracking issue for this feature is: #148739

## const_convert

The tracking issue for this feature is: #143773

## const_default

The tracking issue for this feature is: #143894

## const_drop_in_place

The tracking issue for this feature is: #109342

## const_eval_select

The tracking issue for this feature is: #124625

## const_format_args

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## const_heap

The tracking issue for this feature is: #79597

## const_index

The tracking issue for this feature is: #143775

## const_mul_add

The tracking issue for this feature is: #146724

## const_ops

The tracking issue for this feature is: #143802

## const_option_ops

The tracking issue for this feature is: #143956

## const_range

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## const_range_bounds

The tracking issue for this feature is: #108082

## const_raw_ptr_comparison

The tracking issue for this feature is: #53020

## const_ref_cell

The tracking issue for this feature is: #137844

## const_result_trait_fn

The tracking issue for this feature is: #144211

## const_result_unwrap_unchecked

The tracking issue for this feature is: #148714

## const_select_unpredictable

The tracking issue for this feature is: #145938

## const_slice_from_mut_ptr_range

The tracking issue for this feature is: #89792

## const_slice_from_ptr_range

The tracking issue for this feature is: #89792

## const_slice_make_iter

The tracking issue for this feature is: #137737

## const_split_off_first_last

The tracking issue for this feature is: #138539

## const_swap_with_slice

The tracking issue for this feature is: #142204

## const_type_name

The tracking issue for this feature is: #63084

## container_error_extra

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## context_ext

The tracking issue for this feature is: #123392

## control_flow_into_value

The tracking issue for this feature is: #137461

## control_flow_ok

The tracking issue for this feature is: #140266

## convert_float_to_int

The tracking issue for this feature is: #67057

## copied_into_inner

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## core_float_math

The tracking issue for this feature is: #137578

## core_intrinsics

This feature is internal to the Rust compiler and is not intended for general use.

## core_intrinsics_fallbacks

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## core_io_borrowed_buf

The tracking issue for this feature is: #117693

## core_private_bignum

This feature is internal to the Rust compiler and is not intended for general use.

## core_private_diy_float

This feature is internal to the Rust compiler and is not intended for general use.

## coroutine_trait

The tracking issue for this feature is: #43122

## cow_is_borrowed

The tracking issue for this feature is: #65143

## cstr_bytes

The tracking issue for this feature is: #112115

## cstr_display

The tracking issue for this feature is: #139984

## cstr_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## current_thread_id

The tracking issue for this feature is: #147194

## cursor_split

The tracking issue for this feature is: #86369

## darwin_objc

The tracking issue for this feature is: #145496

## deadline_api

The tracking issue for this feature is: #46316

## debug_closure_helpers

The tracking issue for this feature is: #117729

## dec2flt

This feature is internal to the Rust compiler and is not intended for general use.

## deque_extend_front

The tracking issue for this feature is: #146975

## deref_pure_trait

The tracking issue for this feature is: #87121

## derive_clone_copy

This feature is internal to the Rust compiler and is not intended for general use.

## derive_coerce_pointee

The tracking issue for this feature is: #123430

## derive_const

The tracking issue for this feature is: #118304

## derive_eq

This feature is internal to the Rust compiler and is not intended for general use.

## dir_entry_ext2

The tracking issue for this feature is: #85573

## discriminant_kind

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## disjoint_bitor

The tracking issue for this feature is: #135758

## dispatch_from_dyn

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## downcast_unchecked

The tracking issue for this feature is: #90850

## drain_keep_rest

The tracking issue for this feature is: #101122

## drop_guard

The tracking issue for this feature is: #144426

## duration_constants

The tracking issue for this feature is: #57391

## duration_constructors

The tracking issue for this feature is: #120301

Add the methods from_days and from_weeks to Duration.

## duration_from_nanos_u128

The tracking issue for this feature is: #139201

## duration_millis_float

The tracking issue for this feature is: #122451

## duration_units

The tracking issue for this feature is: #120301

## edition_panic

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## error_generic_member_access

The tracking issue for this feature is: #99301

## error_iter

The tracking issue for this feature is: #58520

## error_reporter

The tracking issue for this feature is: #90172

## error_type_id

The tracking issue for this feature is: #60784

## exact_bitshifts

The tracking issue for this feature is: #144336

## exact_div

The tracking issue for this feature is: #139911

## exact_size_is_empty

The tracking issue for this feature is: #35428

## exclusive_wrapper

The tracking issue for this feature is: #98407

## exit_status_error

The tracking issue for this feature is: #84908

## exitcode_exit_method

The tracking issue for this feature is: #97100

## extend_one

The tracking issue for this feature is: #72631

## extend_one_unchecked

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## fd

This feature is internal to the Rust compiler and is not intended for general use.

## fd_read

This feature is internal to the Rust compiler and is not intended for general use.

## file_buffered

The tracking issue for this feature is: #130804

## float_algebraic

The tracking issue for this feature is: #136469

## float_erf

The tracking issue for this feature is: #136321

## float_gamma

The tracking issue for this feature is: #99842

## float_minimum_maximum

The tracking issue for this feature is: #91079

## flt2dec

This feature is internal to the Rust compiler and is not intended for general use.

## fmt_helpers_for_derive

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## fmt_internals

This feature is internal to the Rust compiler and is not intended for general use.

## fn_ptr_trait

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## fn_traits

The tracking issue for this feature is #29625

See Also: unboxed_closures

The fn_traits feature allows for implementation of the Fn* traits for creating custom closure-like types.

#![feature(unboxed_closures)]
#![feature(fn_traits)]

struct Adder {
    a: u32
}

impl FnOnce<(u32, )> for Adder {
    type Output = u32;
    extern "rust-call" fn call_once(self, b: (u32, )) -> Self::Output {
        self.a + b.0
    }
}

fn main() {
    let adder = Adder { a: 3 };
    assert_eq!(adder(2), 5);
}
## forget_unsized

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## format_args_nl

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## formatting_options

The tracking issue for this feature is: #118117

## freeze

The tracking issue for this feature is: #121675

## fs_set_times

The tracking issue for this feature is: #147455

## funnel_shifts

The tracking issue for this feature is: #145686

## future_join

The tracking issue for this feature is: #91642

## gen_future

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## generic_assert_internals

The tracking issue for this feature is: #44838

## generic_atomic

The tracking issue for this feature is: #130539

## get_disjoint_mut_helpers

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## get_mut_unchecked

The tracking issue for this feature is: #63292

## gethostname

The tracking issue for this feature is: #135142

## hash_set_entry

The tracking issue for this feature is: #60896

## hasher_prefixfree_extras

The tracking issue for this feature is: #96762

## hashmap_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## hint_must_use

The tracking issue for this feature is: #94745

## inplace_iteration

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## int_format_into

The tracking issue for this feature is: #138215

## int_from_ascii

The tracking issue for this feature is: #134821

## int_lowest_highest_one

The tracking issue for this feature is: #145203

## int_roundings

The tracking issue for this feature is: #88581

## integer_atomics

The tracking issue for this feature is: #99069

## internal_impls_macro

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## internal_output_capture

This feature is internal to the Rust compiler and is not intended for general use.

## io_const_error

The tracking issue for this feature is: #133448

## io_const_error_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## io_error_inprogress

The tracking issue for this feature is: #130840

## io_error_more

The tracking issue for this feature is: #86442

## io_error_uncategorized

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## io_slice_as_bytes

The tracking issue for this feature is: #132818

## ip

The tracking issue for this feature is: #27709

## ip_as_octets

The tracking issue for this feature is: #137259

## is_ascii_octdigit

The tracking issue for this feature is: #101288

## is_loongarch_feature_detected

The tracking issue for this feature is: #117425

## is_riscv_feature_detected

The tracking issue for this feature is: #111192

## isolate_most_least_significant_one

The tracking issue for this feature is: #136909

## iter_advance_by

The tracking issue for this feature is: #77404

## iter_array_chunks

The tracking issue for this feature is: #100450

## iter_collect_into

The tracking issue for this feature is: #94780

## iter_from_coroutine

The tracking issue for this feature is: #43122

## iter_intersperse

The tracking issue for this feature is: #79524

## iter_is_partitioned

The tracking issue for this feature is: #62544

## iter_macro

The tracking issue for this feature is: #142269

## iter_map_windows

The tracking issue for this feature is: #87155

## iter_next_chunk

The tracking issue for this feature is: #98326

## iter_order_by

The tracking issue for this feature is: #64295

## iter_partition_in_place

The tracking issue for this feature is: #62543

## iterator_try_collect

The tracking issue for this feature is: #94047

## iterator_try_reduce

The tracking issue for this feature is: #87053

## junction_point

The tracking issue for this feature is: #121709

## layout_for_ptr

The tracking issue for this feature is: #69835

## lazy_cell_into_inner

The tracking issue for this feature is: #125623

## lazy_get

The tracking issue for this feature is: #129333

## legacy_receiver_trait

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## liballoc_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## libstd_sys_internals

This feature is internal to the Rust compiler and is not intended for general use.

## likely_unlikely

The tracking issue for this feature is: #136873

## linked_list_cursors

The tracking issue for this feature is: #58533

## linked_list_remove

The tracking issue for this feature is: #69210

## linked_list_retain

The tracking issue for this feature is: #114135

## linux_pidfd

The tracking issue for this feature is: #82971

## local_key_cell_update

The tracking issue for this feature is: #143989

## local_waker

The tracking issue for this feature is: #118959

## lock_value_accessors

The tracking issue for this feature is: #133407

## log_syntax

The tracking issue for this feature is: #29598

## map_try_insert

The tracking issue for this feature is: #82766

## mapped_lock_guards

The tracking issue for this feature is: #117108

## maybe_uninit_array_assume_init

The tracking issue for this feature is: #96097

## maybe_uninit_as_bytes

The tracking issue for this feature is: #93092

## maybe_uninit_fill

The tracking issue for this feature is: #117428

## maybe_uninit_slice

The tracking issue for this feature is: #63569

## maybe_uninit_uninit_array_transpose

The tracking issue for this feature is: #96097

## maybe_uninit_write_slice

The tracking issue for this feature is: #79995

## mem_conjure_zst

The tracking issue for this feature is: #95383

## mem_copy_fn

The tracking issue for this feature is: #98262

## min_const_control_flow

The tracking issue for this feature is: #148738

## more_float_constants

The tracking issue for this feature is: #146939

## motor_ext

The tracking issue for this feature is: #147456

## mpmc_channel

The tracking issue for this feature is: #126840

## mutex_data_ptr

The tracking issue for this feature is: #140368

## new_range_api

The tracking issue for this feature is: #125687

## next_index

The tracking issue for this feature is: #130711

## nonpoison_condvar

The tracking issue for this feature is: #134645

## nonpoison_mutex

The tracking issue for this feature is: #134645

## nonpoison_rwlock

The tracking issue for this feature is: #134645

## nonzero_bitwise

The tracking issue for this feature is: #128281

## nonzero_from_mut

The tracking issue for this feature is: #106290

## nonzero_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## nonzero_ops

The tracking issue for this feature is: #84186

## normalize_lexically

The tracking issue for this feature is: #134694

## numfmt

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## objc_class_variant

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## objc_selector_variant

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## once_cell_get_mut

The tracking issue for this feature is: #121641

## once_cell_try

The tracking issue for this feature is: #109737

## once_cell_try_insert

The tracking issue for this feature is: #116693

## one_sided_range

The tracking issue for this feature is: #69780

## option_array_transpose

The tracking issue for this feature is: #130828

## option_reduce

The tracking issue for this feature is: #144273

## option_zip

The tracking issue for this feature is: #70086

## os_str_slice

The tracking issue for this feature is: #118485

## os_string_truncate

The tracking issue for this feature is: #133262

## panic_abort

The tracking issue for this feature is: #32837

## panic_always_abort

The tracking issue for this feature is: #84438

## panic_backtrace_config

The tracking issue for this feature is: #93346

## panic_can_unwind

The tracking issue for this feature is: #92988

## panic_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## panic_unwind

The tracking issue for this feature is: #32837

## panic_update_hook

The tracking issue for this feature is: #92649

## partial_ord_chaining_methods

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## path_is_empty

The tracking issue for this feature is: #148494

## path_trailing_sep

The tracking issue for this feature is: #142503

## pattern

The tracking issue for this feature is: #27721

## pattern_type_macro

The tracking issue for this feature is: #123646

## pattern_type_range_trait

The tracking issue for this feature is: #123646

## peekable_next_if_map

The tracking issue for this feature is: #143702

## peer_credentials_unix_socket

The tracking issue for this feature is: #42839

## phantom_variance_markers

The tracking issue for this feature is: #135806

## pin_coerce_unsized_trait

The tracking issue for this feature is: #123430

## pin_derefmut_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## pointer_is_aligned_to

The tracking issue for this feature is: #96284

## pointer_try_cast_aligned

The tracking issue for this feature is: #141221

## portable_simd

The tracking issue for this feature is: #86656

## prelude_future

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## prelude_next

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## print_internals

This feature is internal to the Rust compiler and is not intended for general use.

## proc_macro_def_site

The tracking issue for this feature is: #54724

## proc_macro_diagnostic

The tracking issue for this feature is: #54140

## proc_macro_expand

The tracking issue for this feature is: #90765

## proc_macro_internals

The tracking issue for this feature is: #27812

## proc_macro_quote

The tracking issue for this feature is: #54722

## proc_macro_span

The tracking issue for this feature is: #54725

## proc_macro_totokens

The tracking issue for this feature is: #130977

## proc_macro_tracked_env

The tracking issue for this feature is: #99515

## proc_macro_value

The tracking issue for this feature is: #136652

## process_chroot

The tracking issue for this feature is: #141298

## process_exitcode_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## process_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## process_setsid

The tracking issue for this feature is: #105376

## profiler_runtime_lib

This feature is internal to the Rust compiler and is not intended for general use.

## profiling_marker_api

The tracking issue for this feature is: #148197

## ptr_alignment_type

The tracking issue for this feature is: #102070

## ptr_as_ref_unchecked

The tracking issue for this feature is: #122034

## ptr_as_uninit

The tracking issue for this feature is: #75402

## ptr_cast_array

The tracking issue for this feature is: #144514

## ptr_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## ptr_mask

The tracking issue for this feature is: #98290

## ptr_metadata

The tracking issue for this feature is: #81513

## pub_crate_should_not_need_unstable_attr

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## push_mut

The tracking issue for this feature is: #135974

## random

The tracking issue for this feature is: #130703

## range_bounds_is_empty

The tracking issue for this feature is: #137300

## range_into_bounds

The tracking issue for this feature is: #136903

## raw_os_error_ty

The tracking issue for this feature is: #107792

## raw_slice_split

The tracking issue for this feature is: #95595

## raw_vec_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## read_buf

The tracking issue for this feature is: #78485

## read_buf_at

The tracking issue for this feature is: #140771

## reentrant_lock

The tracking issue for this feature is: #121440

## reentrant_lock_data_ptr

The tracking issue for this feature is: #140368

## refcell_try_map

The tracking issue for this feature is: #143801

## restricted_std

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## result_option_map_or_default

The tracking issue for this feature is: #138099

## rev_into_inner

The tracking issue for this feature is: #144277

## rt

This feature is internal to the Rust compiler and is not intended for general use.

## rwlock_data_ptr

The tracking issue for this feature is: #140368

## sealed

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## seek_io_take_position

The tracking issue for this feature is: #97227

## seek_stream_len

The tracking issue for this feature is: #59359

## set_permissions_nofollow

The tracking issue for this feature is: #141607

## set_ptr_value

The tracking issue for this feature is: #75091

## setgroups

The tracking issue for this feature is: #90747

## sgx_platform

The tracking issue for this feature is: #56975

## sized_type_properties

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## slice_concat_ext

The tracking issue for this feature is: #27747

## slice_concat_trait

The tracking issue for this feature is: #27747

## slice_from_ptr_range

The tracking issue for this feature is: #89792

## slice_index_methods

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## slice_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## slice_iter_mut_as_mut_slice

The tracking issue for this feature is: #93079

## slice_partition_dedup

The tracking issue for this feature is: #54279

## slice_pattern

The tracking issue for this feature is: #56345

## slice_ptr_get

The tracking issue for this feature is: #74265

## slice_range

The tracking issue for this feature is: #76393

## slice_split_once

The tracking issue for this feature is: #112811

## slice_swap_unchecked

The tracking issue for this feature is: #88539

## sliceindex_wrappers

The tracking issue for this feature is: #146179

## smart_pointer_try_map

The tracking issue for this feature is: #144419

## solid_ext

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## sort_floats

The tracking issue for this feature is: #93396

## split_array

The tracking issue for this feature is: #90091

## split_as_slice

The tracking issue for this feature is: #96137

## std_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## stdarch_aarch64_feature_detection

The tracking issue for this feature is: #127764

## stdarch_arm_feature_detection

The tracking issue for this feature is: #111190

## stdarch_internal

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## stdarch_loongarch_feature_detection

The tracking issue for this feature is: #117425

## stdarch_mips_feature_detection

The tracking issue for this feature is: #111188

## stdarch_powerpc_feature_detection

The tracking issue for this feature is: #111191

## stdarch_riscv_feature_detection

The tracking issue for this feature is: #111192

## stdio_makes_pipe

The tracking issue for this feature is: #98288

## step_trait

The tracking issue for this feature is: #42168

## str_as_str

The tracking issue for this feature is: #130366

## str_from_raw_parts

The tracking issue for this feature is: #119206

## str_from_utf16_endian

The tracking issue for this feature is: #116258

## str_internals

This feature is internal to the Rust compiler and is not intended for general use.

## str_lines_remainder

The tracking issue for this feature is: #77998

## str_split_inclusive_remainder

The tracking issue for this feature is: #77998

## str_split_remainder

The tracking issue for this feature is: #77998

## str_split_whitespace_remainder

The tracking issue for this feature is: #77998

## string_from_utf8_lossy_owned

The tracking issue for this feature is: #129436

## string_into_chars

The tracking issue for this feature is: #133125

## string_remove_matches

The tracking issue for this feature is: #72826

## string_replace_in_place

The tracking issue for this feature is: #147949

## strip_circumfix

The tracking issue for this feature is: #147946

## substr_range

The tracking issue for this feature is: #126769

## sync_nonpoison

The tracking issue for this feature is: #134645

## sync_poison_mod

The tracking issue for this feature is: #134646

## sync_unsafe_cell

The tracking issue for this feature is: #95439

## tcp_deferaccept

The tracking issue for this feature is: #119639

## tcp_linger

The tracking issue for this feature is: #88494

## tcplistener_into_incoming

The tracking issue for this feature is: #88373

## temporary_niche_types

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## test

The tracking issue for this feature is: None.

The internals of the test crate are unstable, behind the test flag. The most widely used part of the test crate are benchmark tests, which can test the performance of your code. Let's make our src/lib.rs look like this (comments elided):

#![feature(test)]

extern crate test;

pub fn add_two(a: i32) -> i32 {
    a + 2
}

#[cfg(test)]
mod tests {
    use super::*;
    use test::Bencher;

    #[test]
    fn it_works() {
        assert_eq!(4, add_two(2));
    }

    #[bench]
    fn bench_add_two(b: &mut Bencher) {
        b.iter(|| add_two(2));
    }
}
Note the test feature gate, which enables this unstable feature.

We've imported the test crate, which contains our benchmarking support. We have a new function as well, with the bench attribute. Unlike regular tests, which take no arguments, benchmark tests take a &mut Bencher. This Bencher provides an iter method, which takes a closure. This closure contains the code we'd like to benchmark.

We can run benchmark tests with cargo bench:

$ cargo bench
   Compiling adder v0.0.1 (file:///home/steve/tmp/adder)
     Running target/release/adder-91b3e234d4ed382a

running 2 tests
test tests::it_works ... ignored
test tests::bench_add_two ... bench:         1 ns/iter (+/- 0)

test result: ok. 0 passed; 0 failed; 1 ignored; 1 measured
Our non-benchmark test was ignored. You may have noticed that cargo bench takes a bit longer than cargo test. This is because Rust runs our benchmark a number of times, and then takes the average. Because we're doing so little work in this example, we have a 1 ns/iter (+/- 0), but this would show the variance if there was one.

Advice on writing benchmarks:

Move setup code outside the iter loop; only put the part you want to measure inside
Make the code do "the same thing" on each iteration; do not accumulate or change state
Make the outer function idempotent too; the benchmark runner is likely to run it many times
Make the inner iter loop short and fast so benchmark runs are fast and the calibrator can adjust the run-length at fine resolution
Make the code in the iter loop do something simple, to assist in pinpointing performance improvements (or regressions)
Gotcha: optimizations

There's another tricky part to writing benchmarks: benchmarks compiled with optimizations activated can be dramatically changed by the optimizer so that the benchmark is no longer benchmarking what one expects. For example, the compiler might recognize that some calculation has no external effects and remove it entirely.

#![feature(test)]

extern crate test;
use test::Bencher;

#[bench]
fn bench_xor_1000_ints(b: &mut Bencher) {
    b.iter(|| {
        (0..1000).fold(0, |old, new| old ^ new);
    });
}
gives the following results

running 1 test
test bench_xor_1000_ints ... bench:         0 ns/iter (+/- 0)

test result: ok. 0 passed; 0 failed; 0 ignored; 1 measured
The benchmarking runner offers two ways to avoid this. Either, the closure that the iter method receives can return an arbitrary value which forces the optimizer to consider the result used and ensures it cannot remove the computation entirely. This could be done for the example above by adjusting the b.iter call to

b.iter(|| {
    // Note lack of `;` (could also use an explicit `return`).
    (0..1000).fold(0, |old, new| old ^ new)
});
Or, the other option is to call the generic test::black_box function, which is an opaque "black box" to the optimizer and so forces it to consider any argument as used.

#![feature(test)]

extern crate test;

b.iter(|| {
    let n = test::black_box(1000);

    (0..n).fold(0, |a, b| a ^ b)
})
Neither of these read or modify the value, and are very cheap for small values. Larger values can be passed indirectly to reduce overhead (e.g. black_box(&huge_struct)).

Performing either of the above changes gives the following benchmarking results

running 1 test
test bench_xor_1000_ints ... bench:       131 ns/iter (+/- 3)

test result: ok. 0 passed; 0 failed; 0 ignored; 1 measured
However, the optimizer can still modify a testcase in an undesirable manner even when using either of the above.

## thin_box

The tracking issue for this feature is: #92791

## thread_id_value

The tracking issue for this feature is: #67939

## thread_local_internals

This feature is internal to the Rust compiler and is not intended for general use.

## thread_raw

The tracking issue for this feature is: #97523

## thread_sleep_until

The tracking issue for this feature is: #113752

## thread_spawn_hook

The tracking issue for this feature is: #132951

## trace_macros

The tracking issue for this feature is #29598.

With trace_macros you can trace the expansion of macros in your code.

Examples

#![feature(trace_macros)]

fn main() {
    trace_macros!(true);
    println!("Hello, Rust!");
    trace_macros!(false);
}
The cargo build output:

note: trace_macro
 --> src/main.rs:5:5
  |
5 |     println!("Hello, Rust!");
  |     ^^^^^^^^^^^^^^^^^^^^^^^^^
  |
  = note: expanding `println! { "Hello, Rust!" }`
  = note: to `print ! ( concat ! ( "Hello, Rust!" , "\n" ) )`
  = note: expanding `print! { concat ! ( "Hello, Rust!" , "\n" ) }`
  = note: to `$crate :: io :: _print ( format_args ! ( concat ! ( "Hello, Rust!" , "\n" ) )
          )`

    Finished dev [unoptimized + debuginfo] target(s) in 0.60 secs
## track_path

The tracking issue for this feature is: #99515

## transmutability

The tracking issue for this feature is: #99571

## trim_prefix_suffix

The tracking issue for this feature is: #142312

## trivial_clone

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## trusted_fused

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## trusted_len

The tracking issue for this feature is: #37572

## trusted_len_next_unchecked

The tracking issue for this feature is: #37572

## trusted_random_access

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## trusted_step

The tracking issue for this feature is: #85731

## try_find

The tracking issue for this feature is: #63178

## try_reserve_kind

The tracking issue for this feature is: #48043

## try_trait_v2

The tracking issue for this feature is: #84277

## try_trait_v2_residual

The tracking issue for this feature is: #91285

## try_trait_v2_yeet

The tracking issue for this feature is: #96374

## try_with_capacity

The tracking issue for this feature is: #91913

## tuple_trait

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## type_ascription

The tracking issue for this feature is: #23416

## ub_checks

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## uefi_std

The tracking issue for this feature is: #100499

## uint_bit_width

The tracking issue for this feature is: #142326

## unchecked_neg

The tracking issue for this feature is: #85122

## unchecked_shifts

The tracking issue for this feature is: #85122

## unicode_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## unique_rc_arc

The tracking issue for this feature is: #112566

## unix_file_vectored_at

The tracking issue for this feature is: #89517

## unix_mkfifo

The tracking issue for this feature is: #139324

## unix_send_signal

The tracking issue for this feature is: #141975

## unix_set_mark

The tracking issue for this feature is: #96467

## unix_socket_ancillary_data

The tracking issue for this feature is: #76915

## unix_socket_exclbind

The tracking issue for this feature is: #123481

## unix_socket_peek

The tracking issue for this feature is: #76923

## unsafe_cell_access

The tracking issue for this feature is: #136327

## unsafe_pinned

The tracking issue for this feature is: #125735

## unsize

The tracking issue for this feature is: #18598

## unwrap_infallible

The tracking issue for this feature is: #61695

## update_panic_count

This feature is internal to the Rust compiler and is not intended for general use.

## utf16_extra

The tracking issue for this feature is: #94919

## variant_count

The tracking issue for this feature is: #73662

## vec_deque_extract_if

The tracking issue for this feature is: #147750

## vec_deque_iter_as_slices

The tracking issue for this feature is: #123947

## vec_deque_truncate_front

The tracking issue for this feature is: #140667

## vec_into_chunks

The tracking issue for this feature is: #142137

## vec_into_raw_parts

The tracking issue for this feature is: #65816

## vec_peek_mut

The tracking issue for this feature is: #122742

## vec_push_within_capacity

The tracking issue for this feature is: #100486

## vec_split_at_spare

The tracking issue for this feature is: #81944

## vec_try_remove

The tracking issue for this feature is: #146954

## waker_from_fn_ptr

The tracking issue for this feature is: #148457

## wasi_ext

The tracking issue for this feature is: #71213

## windows_by_handle

The tracking issue for this feature is: #63010

## windows_c

This feature is internal to the Rust compiler and is not intended for general use.

## windows_change_time

The tracking issue for this feature is: #121478

## windows_handle

This feature is internal to the Rust compiler and is not intended for general use.

## windows_net

This feature is internal to the Rust compiler and is not intended for general use.

## windows_process_exit_code_from

The tracking issue for this feature is: #111688

## windows_process_extensions_async_pipes

The tracking issue for this feature is: #98289

## windows_process_extensions_force_quotes

The tracking issue for this feature is: #82227

## windows_process_extensions_inherit_handles

The tracking issue for this feature is: #146407

## windows_process_extensions_main_thread_handle

The tracking issue for this feature is: #96723

## windows_process_extensions_raw_attribute

The tracking issue for this feature is: #114854

## windows_process_extensions_show_window

The tracking issue for this feature is: #127544

## windows_process_extensions_startupinfo

The tracking issue for this feature is: #141010

## windows_stdio

This feature is internal to the Rust compiler and is not intended for general use.

## wrapping_int_impl

The tracking issue for this feature is: #32463

## wrapping_next_power_of_two

The tracking issue for this feature is: #32463

## write_all_vectored

The tracking issue for this feature is: #70436

## wtf8_internals

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.

## yeet_desugar_details

This feature has no tracking issue, and is therefore likely internal to the compiler, not being intended for general use.
