/*
   Copyright (c) 2013 Broadcom Corporation
   All Rights Reserved

    <:label-BRCM:2013:DUAL/GPL:standard
    
    Unless you and Broadcom execute a separate written software license
    agreement governing use of this software, this software is licensed
    to you under the terms of the GNU General Public License version 2
    (the "GPL"), available at http://www.broadcom.com/licenses/GPLv2.php,
    with the following added to such license:
    
       As a special exception, the copyright holders of this software give
       you permission to link this software with independent modules, and
       to copy and distribute the resulting executable under terms of your
       choice, provided that you also meet, for each linked independent
       module, the terms and conditions of the license of that module.
       An independent module is a module which is not derived from this
       software.  The special exception does not apply to any modifications
       of the software.
    
    Not withstanding the above, under no circumstances may you combine
    this software in any way with any other Broadcom software provided
    under a license other than the GPL, without Broadcom's express prior
    written consent.
    
    :> 
*/             

#ifndef __ACCESS_MACROS_H_INCLUDED
#define __ACCESS_MACROS_H_INCLUDED
#endif
typedef unsigned char uint8_t;
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;

#define RUNNER_BASE_ADDRESS 0xa0000000

/* The following group of macros are intended for shared/io memory access
*/

#define MGET_8(a )              ( *(volatile uint8_t* )(a) )
#define MGET_16(a)              ( *(volatile uint16_t*)(a) )
#define MGET_32(a)              ( *(volatile uint32_t*)(a) )

#define MREAD_8( a, r)			( (r) = MGET_8( a ) )
#define MREAD_16(a, r)			( (r) = MGET_16( a ) )
#define MREAD_32(a, r)			( (r) = MGET_32( a ) )

#define MWRITE_8( a, r )        ( *(volatile uint8_t *)(a) = (uint8_t) (r))
#define MWRITE_16( a, r )       ( *(volatile uint16_t*)(a) = (uint16_t)(r))
#define MWRITE_32( a, r )       ( *(volatile uint32_t*)(a) = (uint32_t)(r))

#define MGET_I_8( a, i)         ( *((volatile uint8_t *)(a) + (i)) )
#define MGET_I_16(a, i)         ( *((volatile uint16_t*)(a) + (i)) )
#define MGET_I_32(a, i)         ( *((volatile uint32_t*)(a) + (i)) )

#define MREAD_I_8( a, i, r)		( (r) = MGET_I_8( (a),(i)) )
#define MREAD_I_16(a, i, r)		( (r) = MGET_I_16((a),(i)) )
#define MREAD_I_32(a, i, r)		( (r) = MGET_I_32((a),(i)) )

#define MWRITE_I_8( a, i, r)    ( *((volatile uint8_t *)(a) + (i)) = (uint8_t) (r))
#define MWRITE_I_16(a, i, r)    ( *((volatile uint16_t*)(a) + (i)) = (uint16_t)(r)) 
#define MWRITE_I_32(a, i, r)    ( *((volatile uint32_t*)(a) + (i)) = (uint32_t)(r))

/* Set block of shared memory to the specified value */
#define MEMSET(a, v, sz)				memset(a, v, sz)

/* Copy memory block local memory --> shared memory */
#define MWRITE_BLK_8(d, s, sz )      memcpy(d, s, sz)
#define MWRITE_BLK_16(d, s, sz)      { uint32_t i, val; for ( i = 0; i < ( sz / 2 ); i++ ){ val = *((volatile uint16_t*)(s) + (i)); MWRITE_I_16( d, i, val ); } }
#define MWRITE_BLK_32(d, s, sz)      { uint32_t i, val; for ( i = 0; i < ( sz / 4 ); i++ ){ val = *((volatile uint32_t*)(s) + (i)); MWRITE_I_32( d, i, val ); } }

/* Copy memory block shared memory --> local memory */
#define MREAD_BLK_8(d, s, sz )   	memcpy(d, s, sz)
#define MREAD_BLK_16(d, s, sz)  		memcpy(d, s, sz)
#define MREAD_BLK_32(d, s, sz)  		memcpy(d, s, sz)

/* Bit-field access macros
: v		-  value
: lsbn	- ls_bit_number
: fw	- field_width
: a     - address
: rv	- read_value
 */
#define FIELD_GET(v, lsbn, fw)			( ((v)>>(lsbn)) & ((1 << (fw)) - 1) )

#define FIELD_MGET_32(a, lsbn, fw)		( FIELD_GET( MGET_32(a), (lsbn), (fw)) )
#define FIELD_MGET_16(a, lsbn, fw)    	( FIELD_GET( MGET_16(a), (lsbn), (fw)) )
#define FIELD_MGET_8( a, lsbn, fw)		( FIELD_GET( MGET_8(a) , (lsbn), (fw)) )

#define FIELD_MREAD_8( a, lsbn, fw, rv)	( rv = FIELD_MGET_8( (a),   (lsbn), (fw)) )
#define FIELD_MREAD_16(a, lsbn, fw, rv)	( rv = FIELD_MGET_16((a),   (lsbn), (fw)) )
#define FIELD_MREAD_32(a, lsbn, fw, rv)	( rv = FIELD_MGET_32((a),   (lsbn), (fw)) )


#define FIELD_SET( value, ls_bit_number, field_width, write_value ) \
         do {                                                          \
            uint32_t  mask;                                          \
            mask = ( ( 1 << (field_width) ) - 1 ) << (ls_bit_number);  \
            value &=  ~mask;                                           \
            value |= (write_value) << (ls_bit_number);                 \
        }while(0)

#define FIELD_MWRITE_32( address, ls_bit_number, field_width, write_value )		\
        do {                                                              			\
            uint32_t  current_value = MGET_32(address);            			\
            FIELD_SET(current_value, ls_bit_number, field_width, write_value );	\
            MWRITE_32(address, current_value);                   				\
        }while(0)

#define FIELD_MWRITE_16( address, ls_bit_number, field_width, write_value)  		\
        do{                                                              			\
            uint16_t  current_value = MGET_16(address);            			\
            FIELD_SET(current_value, ls_bit_number, field_width, write_value);	\
            MWRITE_16(address, current_value);                     				\
        }while(0)

#define FIELD_MWRITE_8( address, ls_bit_number, field_width, write_value )   	\
        do{                                                              			\
            uint16_t  current_value = MGET_8(address);             			\
            FIELD_SET(current_value, ls_bit_number, field_width, write_value);	\
            MWRITE_8(address, current_value);                      				\
        }while(0)


/*#endif  __ACCESS_MACROS_H_INCLUDED */


