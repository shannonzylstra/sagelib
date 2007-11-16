r"""
Ideals

SAGE provides functionality for computing with ideals.  One can create
an ideal in any commutative ring $R$ by giving a list of generators,
using the notation \code{R.ideal([a,b,...])}.
"""

#*****************************************************************************
#       Copyright (C) 2005 William Stein <wstein@gmail.com>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#
#    This code is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    General Public License for more details.
#
#  The full text of the GPL is available at:
#
#                  http://www.gnu.org/licenses/
#*****************************************************************************

import sage.misc.latex as latex
import sage.rings.ring
import sage.rings.principal_ideal_domain
import commutative_ring
from sage.structure.sage_object import SageObject
from sage.structure.element import MonoidElement
from sage.interfaces.singular import singular as singular_default, is_SingularElement
import sage.rings.infinity
from sage.structure.sequence import Sequence

def Ideal(R, gens=[], coerce=True):
    r"""
    Create the ideal in ring with given generators.

    There are some shorthand notations for creating an ideal, in addition
    to use the Ideal function:
    \begin{verbatim}
        --  R.ideal(gens, coerce=True)
        --  gens*R
        --  R*gens
    \end{verbatim}        

    INPUT:
        R -- a ring
        gens -- list of elements
        coerce -- bool (default: True); whether gens need to be coerced into ring.

    Alternatively, one can also call this function with the syntax
         Ideal(gens)
    where gens is a nonempty list of generators or a single generator.
        
    OUTPUT:
        The ideal of ring generated by gens.

    EXAMPLES:
        sage: R, x = PolynomialRing(ZZ, 'x').objgen()
        sage: I = R.ideal([4 + 3*x + x^2, 1 + x^2])
        sage: I
        Ideal (x^2 + 3*x + 4, x^2 + 1) of Univariate Polynomial Ring in x over Integer Ring
        sage: Ideal(R, [4 + 3*x + x^2, 1 + x^2])
        Ideal (x^2 + 3*x + 4, x^2 + 1) of Univariate Polynomial Ring in x over Integer Ring
        sage: Ideal((4 + 3*x + x^2, 1 + x^2))
        Ideal (x^2 + 3*x + 4, x^2 + 1) of Univariate Polynomial Ring in x over Integer Ring
        
        sage: ideal(x^2-2*x+1, x^2-1)
        Ideal (x^2 - 1, x^2 - 2*x + 1) of Univariate Polynomial Ring in x over Integer Ring
        sage: ideal([x^2-2*x+1, x^2-1])
        Ideal (x^2 - 1, x^2 - 2*x + 1) of Univariate Polynomial Ring in x over Integer Ring


    This example illustrates how SAGE finds a common ambient ring for the ideal, even though
    1 is in the integers (in this case).
        sage: R.<t> = ZZ['t']
        sage: i = ideal(1,t,t^2)
        sage: i
        Ideal (t^2, 1, t) of Univariate Polynomial Ring in t over Integer Ring
        sage: ideal(1/2,t,t^2)
        Principal ideal (1) of Univariate Polynomial Ring in t over Rational Field

    TESTS:
        sage: R, x = PolynomialRing(ZZ, 'x').objgen()
        sage: I = R.ideal([4 + 3*x + x^2, 1 + x^2])
        sage: I == loads(dumps(I))
        True

        sage: I = Ideal(R, [4 + 3*x + x^2, 1 + x^2])
        sage: I == loads(dumps(I))
        True
                
        sage: I = Ideal((4 + 3*x + x^2, 1 + x^2))
        sage: I == loads(dumps(I))
        True

    """
    if isinstance(R, Ideal_generic):
        return Ideal(R.ring(), R.gens())
    
    if isinstance(R, (list, tuple)) and len(R) > 0:
        R = Sequence(R)
        if not isinstance(R.universe(), sage.rings.ring.Ring):
            raise TypeError, "unable to find common ring into which all ideal generators map"
        return R[0].parent().ideal(R)

    if not isinstance(R, sage.rings.ring.Ring):
        try:
            S = R.parent()
        except AttributeError:
            raise TypeError, "ring must be a ring, list, or element."
        if isinstance(S, sage.rings.ring.Ring):
            return Ideal(S, [R])
        else:
            raise TypeError, "ring must be a ring, list, or element."

    if not commutative_ring.is_CommutativeRing(R):
        raise TypeError, "R must be a commutative ring"
    
    if isinstance(gens, Ideal_generic):
        gens = gens.gens()

    if not isinstance(gens, (list, tuple)):
        gens = [R(gens)]
        coerce = False
        
    elif len(gens) == 0:
        gens = [R(0)]
        coerce = False

    if coerce:
        gens = [R(g) for g in gens]

    gens = list(set(gens))
    if isinstance(R, sage.rings.principal_ideal_domain.PrincipalIdealDomain):
        # Use GCD algorithm to obtain a principal ideal
        g = gens[0]
        for h in gens[1:]:
            g = R.gcd(g, h)
        return Ideal_pid(R, g)

    if len(gens) == 1:
        return Ideal_principal(R, gens[0])
    
    return Ideal_generic(R, gens, coerce=False)

def is_Ideal(x):
    return isinstance(x, Ideal_generic)

    
class Ideal_generic(MonoidElement):
    """
    An ideal.
    """
    def __init__(self, ring, gens, coerce=True):
        self.__ring = ring
        if not isinstance(gens, (list, tuple)):
            gens = [gens]
        if coerce:
            gens = [ring(x) for x in gens]

        self.__gens = tuple(gens)
        MonoidElement.__init__(self, ring.ideal_monoid())

    def _repr_short(self):
        return '(%s)'%(', '.join([str(x) for x in self.gens()]))
        
    def __repr__(self):
        return "Ideal %s of %s"%(self._repr_short(), self.ring())

    def __cmp__(self, other):
        S = set(self.gens())
        T = set(other.gens())
        if S == T:
            return 0
        return cmp(self.gens(), other.gens())

    def __contains__(self, x):
        try:
            return self._contains_(self.__ring(x))
        except TypeError:
            return False

    def _contains_(self, x):
        # check if x, which is assumed to be in the ambient ring, is actually in this ideal.
        raise NotImplementedError

    def __nonzero__(self):
        return self.gens() != [self.ring()(0)]

    def base_ring(self):
        return self.ring().base_ring()

    def _latex_(self):
        return '\\left(%s\\right)%s'%(", ".join([latex.latex(g) for g in \
                                                 self.gens()]),
                                      latex.latex(self.ring()))

    def ring(self):
        """
        Return the ring in which this ideal is contained.
        """
        return self.__ring

    def reduce(self, f):
        r"""
        Return the reduction the element of $f$ modulo the ideal $I$
        (=self).  This is an element of $R$ that is equivalent modulo
        $I$ to $f$.

        EXAMPLES:
            sage: ZZ.ideal(5).reduce(17)
            2
            sage: parent(ZZ.ideal(5).reduce(17))
            Integer Ring
        """
        return f       # default

    def gens(self):
        """
        Return a set of generators / a basis of self. This is usually
        the set of generators provided during object creation.

        EXAMPLE:
            sage: P.<x,y> = PolynomialRing(QQ,2)
            sage: I = Ideal([x,y+1]); I
            Ideal (x, y + 1) of Multivariate Polynomial Ring in x, y over Rational Field
            sage: I.gens()
            (x, y + 1)

            sage: ZZ.ideal(5,10).gens()
            (5,)
        """
        return self.__gens

    def gens_reduced(self):
        r"""
        Same as gens() for this ideal, since there is currently no
        special gens_reduced algorithm implemented for this ring.

        This method is provided so that ideals in ZZ have the method
        gens_reduced(), just like ideals of number fields.

        EXAMPLES:
            sage: ZZ.ideal(5).gens_reduced()
            (5,)
        """
        return self.gens()

    def is_maximal(self):
        raise NotImplementedError

    def is_prime(self):
        raise NotImplementedError

    def is_principal(self):
        if len(self.gens()) <= 1:
            return True
        raise NotImplementedError
        
    def is_trivial(self):
        if self.is_zero():
            return True
        elif self.is_principal():
            return self.gen().is_unit()
        raise NotImplementedError

    def category(self):
        """
        Return the category of this ideal.

        
        """
        import sage.categories.all 
        return sage.categories.all.Ideals(self.__ring)

    def __add__(self, other):
        if not isinstance(other, Ideal_generic):
            other = self.ring().ideal(other)
        return self.ring().ideal(self.gens() + other.gens())
    
    def __radd__(self, other):
        if not isinstance(other, Ideal_generic):
            other = self.ring().ideal(other)
        return self.ring().ideal(self.gens() + other.gens())

    def __mul__(self, other):
        if not isinstance(other, Ideal_generic):
            other = self.ring().ideal(other)
        return self.ring().ideal([x*y for x in self.gens() for y in other.gens()])

    def __rmul__(self, other):
        if not isinstance(other, Ideal_generic):
            other = self.ring().ideal(other)
        return self.ring().ideal([y*x for x in self.gens() for y in other.gens()])
    
    
class Ideal_principal(Ideal_generic):
    """
    A principal ideal.
    """
    def __init__(self, ring, gen):
        Ideal_generic.__init__(self, ring, [gen])

    def __repr__(self):
        return "Principal ideal (%s) of %s"%(self.gen(), self.ring())

    def is_principal(self):
        return True

    def gen(self):
        return self.gens()[0]
    
    def __contains__(self, x):
        if self.gen().is_zero():
            return x.is_zero()
        return self.gen().divides(x)
    
    def __cmp__(self, other):
        if not isinstance(other, Ideal_generic):
            other = self.ring().ideal(other)

        if not other.is_principal():
            return -1
        
        if self.is_zero():
            if not other.is_zero():
                return -1
            return 0

        # is other.gen() / self.gen() a unit in the base ring?
        g0 = other.gen()
        g1 = self.gen()
        if g0.divides(g1) and g1.divides(g0):
            return 0
        return 1

    def divides(self, other):
        """
        Returns True if self divides other.
        """
        if isinstance(other, Ideal_principal):
            return self.gen().divides(other.gen())
        raise NotImplementedError
            
class Ideal_pid(Ideal_principal):
    """
    An ideal of a principal ideal domain.
    """
    def __init__(self, ring, gen):
        Ideal_principal.__init__(self, ring, gen)

    def __add__(self, other):
        if not isinstance(other, Ideal_generic):
            other = self.ring().ideal(other)
        return self.ring().ideal(self.gcd(other))

    def reduce(self, f):
        """
        Return the reduction of f modulo self.
        
        EXAMPLES:
            sage: I = 8*ZZ
            sage: I.reduce(10)
            2
            sage: n = 10; n.mod(I)
            2
        """
        f = self.ring()(f)
        if self.gen() == 0:
            return f
        q, r = f.quo_rem(self.gen())
        return r
        
    def gcd(self, other):
        if isinstance(other, Ideal_principal):
            return self.ring().ideal(self.gen().gcd(other.gen()))
        elif self.gen() in other:
            return other
        else:
            raise NotImplementedError

class Ideal_fractional(Ideal_generic):
    def __init__(self, ring, gen):
        Ideal_generic.__init__(self, ring, [gen])
    def __repr__(self):
        return "Fractional ideal %s of %s"%(self._repr_short(), self.ring())
    


# constructors for standard (benchmark) ideals, written uppercase as
# these are constructors

def Cyclic(R, n=None, homog=False, singular=singular_default):
    """
    ideal of cyclic n-roots from 1-st n variables of R if R is
    coercable to Singular. If n==None n is set to R.ngens()

    INPUT:
        R -- base ring to construct ideal for
        n -- number of cyclic roots (default: None)
        homog -- if True a homogenous ideal is returned using the last
                 variable in the ideal (default: False)
        singular -- singular instance to use

    \note{R will be set as the active ring in Singular}
    """
    if n:
        if n > R.ngens():
            raise ArithmeticError, "n must be <= R.ngens()"
    else:
        n = R.ngens()
    
    singular.lib("poly")
    R._singular_().set_ring()
    if not homog:
        I = singular.cyclic(n)
    else:
        I = singular.cyclic(n).homog(R.gen(n-1))
    return R.ideal(I)


def Katsura(R, n=None, homog=False, singular=singular_default):
    """
    n-th katsura ideal of R if R is coercable to Singular.  If n==None
    n is set to R.ngens()

    INPUT:
        R -- base ring to construct ideal for
        n -- which katsura ideal of R
        homog -- if True a homogenous ideal is returned using the last
                 variable in the ideal (default: False)
        singular -- singular instance to use
    """
    if n:
        if n > R.ngens():
            raise ArithmeticError, "n must be <= R.ngens()"
    else:
        n = R.ngens()
    singular.lib("poly")
    R._singular_().set_ring()
    if not homog:
        I = singular.katsura(n)
    else:
        I = singular.katsura(n).homog(R.gen(n-1))
    return R.ideal(I)
    
def FieldIdeal(R):
    """
    Let q = R.base_ring().order() and (x0,...,x_n) = R.gens() then if
    q is finite this constructor returns
    
    $\langle x_0^q - x_0, \dots , x_n^q - x_n \rangle.$

    We call this ideal the field ideal and the generators the field
    equations.
    """

    q = R.base_ring().order()

    if q is sage.rings.infinity.infinity:
        raise TypeError, "Cannot construct field ideal for R.base_ring().order()==infinity"

    return R.ideal([x**q - x for x in R.gens() ])
